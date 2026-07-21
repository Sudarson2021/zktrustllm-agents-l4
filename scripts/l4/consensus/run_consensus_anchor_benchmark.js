/*
 * run_consensus_anchor_benchmark.js
 * Consensus-layer sensitivity benchmark for the Stage3AnomalyLedger audit
 * micro-benchmark: identical Solidity bytecode deployed and exercised on
 * (a) Ethereum Sepolia (Proof-of-Stake, Gasper) and
 * (b) BNB Smart Chain testnet (Proof-of-Staked-Authority, delegated-staking
 *     BFT family commonly grouped with DPoS).
 *
 * Measures, per network: deploy gas, R repeated anchor commits with
 * wall-clock submit->inclusion latency, receipt gas, block numbers and
 * chain timestamps (for observed inter-block cadence), effective gas price
 * (recorded, boundary-labelled), and the three negative-security rejections
 * (replay, zero-anchor, unauthorized submitter) via staticCall.
 *
 * Usage:
 *   REPEATS=20 npx hardhat run scripts/l4/consensus/run_consensus_anchor_benchmark.js --network sepolia
 *   REPEATS=20 npx hardhat run scripts/l4/consensus/run_consensus_anchor_benchmark.js --network bscTestnet
 *
 * Output: runtime_artifacts/consensus/<network>/<UTC-stamp>/
 *   commits.jsonl  (one row per anchor)
 *   summary.json   (aggregates + negative-security results + file sha256)
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { ethers, network } = require("hardhat");

const ALLOWED = { sepolia: "PoS (Ethereum Gasper)", bscTestnet: "PoSA (delegated-staking BFT / DPoS family)" };

function pctile(sorted, p) {
  if (sorted.length === 0) return null;
  const idx = Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1);
  return sorted[Math.max(0, idx)];
}

async function main() {
  if (!(network.name in ALLOWED)) {
    throw new Error(`Run with --network sepolia or --network bscTestnet (got: ${network.name})`);
  }
  const repeats = parseInt(process.env.REPEATS || "20", 10);
  const [admin] = await ethers.getSigners();
  const chainId = Number((await ethers.provider.getNetwork()).chainId);
  const balance = await ethers.provider.getBalance(admin.address);
  console.log(`KPI_CONSENSUS_NETWORK=${network.name}`);
  console.log(`KPI_CONSENSUS_CHAIN_ID=${chainId}`);
  console.log(`KPI_CONSENSUS_ADMIN=${admin.address}`);
  console.log(`KPI_CONSENSUS_ADMIN_BALANCE_WEI=${balance.toString()}`);
  if (balance === 0n) {
    throw new Error(`Zero balance on ${network.name}. Fund ${admin.address} from the testnet faucet first.`);
  }

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const outDir = path.join("runtime_artifacts", "consensus", network.name, stamp);
  fs.mkdirSync(outDir, { recursive: true });
  const rowsPath = path.join(outDir, "commits.jsonl");

  // ---- deploy the identical audit micro-benchmark ----
  const Ledger = await ethers.getContractFactory("Stage3AnomalyLedger");
  const t0 = Date.now();
  const ledger = await Ledger.deploy(admin.address);
  const deployReceipt = await ledger.deploymentTransaction().wait();
  const deployMs = Date.now() - t0;
  const ledgerAddress = await ledger.getAddress();
  console.log(`KPI_CONSENSUS_LEDGER_ADDRESS=${ledgerAddress}`);
  console.log(`KPI_CONSENSUS_DEPLOY_TX=${deployReceipt.hash}`);
  console.log(`KPI_CONSENSUS_DEPLOY_GAS=${deployReceipt.gasUsed.toString()}`);

  // ---- R timed anchor commits ----
  const rows = [];
  for (let i = 0; i < repeats; i++) {
    const tag = `consensus-${network.name}-${stamp}-${i}`;
    const commitment = ethers.keccak256(ethers.toUtf8Bytes(`${tag}-commitment`));
    const evidenceHash = ethers.keccak256(ethers.toUtf8Bytes(`${tag}-evidence`));
    const tSubmit = Date.now();
    const tx = await ledger.commit(commitment, evidenceHash);
    const receipt = await tx.wait(1);
    const tIncluded = Date.now();
    const block = await ethers.provider.getBlock(receipt.blockNumber);
    const row = {
      i,
      commit_tx: receipt.hash,
      anchor_gas: receipt.gasUsed.toString(),
      effective_gas_price_wei: receipt.gasPrice ? receipt.gasPrice.toString() : null,
      block_number: receipt.blockNumber,
      block_timestamp_utc: block ? block.timestamp : null,
      inclusion_latency_ms: tIncluded - tSubmit
    };
    rows.push(row);
    fs.appendFileSync(rowsPath, JSON.stringify(row) + "\n");
    console.log(`KPI_CONSENSUS_COMMIT_${i}_GAS=${row.anchor_gas} LATENCY_MS=${row.inclusion_latency_ms} BLOCK=${row.block_number}`);
  }

  // ---- negative-security invariants (same pattern as Stage 4 Sepolia script) ----
  const last = rows[rows.length - 1];
  const lastCommitment = ethers.keccak256(
    ethers.toUtf8Bytes(`consensus-${network.name}-${stamp}-${repeats - 1}-commitment`)
  );
  const someEvidence = ethers.keccak256(ethers.toUtf8Bytes(`${stamp}-neg-evidence`));
  let replayRejected = false;
  try { await ledger.commit.staticCall(lastCommitment, someEvidence); } catch { replayRejected = true; }
  let zeroRejected = false;
  try { await ledger.commit.staticCall(ethers.ZeroHash, someEvidence); } catch { zeroRejected = true; }
  const attacker = ethers.Wallet.createRandom().connect(ethers.provider);
  let unauthorizedRejected = false;
  try {
    await ledger.connect(attacker).commit.staticCall(
      ethers.keccak256(ethers.toUtf8Bytes(`${stamp}-attacker`)), someEvidence);
  } catch { unauthorizedRejected = true; }
  console.log(`KPI_CONSENSUS_REPLAY_REJECTED=${replayRejected}`);
  console.log(`KPI_CONSENSUS_ZERO_ANCHOR_REJECTED=${zeroRejected}`);
  console.log(`KPI_CONSENSUS_UNAUTHORIZED_SUBMITTER_REJECTED=${unauthorizedRejected}`);

  // ---- aggregates (all derived from measured rows only) ----
  const lat = rows.map(r => r.inclusion_latency_ms).sort((a, b) => a - b);
  const gasSet = [...new Set(rows.map(r => r.anchor_gas))];
  const ts = rows.map(r => r.block_timestamp_utc).filter(t => t !== null);
  const blockDeltas = [];
  for (let i = 1; i < ts.length; i++) if (ts[i] > ts[i - 1]) blockDeltas.push(ts[i] - ts[i - 1]);
  blockDeltas.sort((a, b) => a - b);

  const summary = {
    benchmark: "consensus_anchor_comparison_v1",
    network: network.name,
    consensus_family: ALLOWED[network.name],
    chain_id: chainId,
    repeats,
    ledger_address: ledgerAddress,
    deploy_tx: deployReceipt.hash,
    deploy_gas: deployReceipt.gasUsed.toString(),
    deploy_wallclock_ms: deployMs,
    anchor_gas_values: gasSet,
    anchor_gas_constant: gasSet.length === 1,
    inclusion_latency_ms: {
      n: lat.length,
      min: lat[0], median: pctile(lat, 50), p95: pctile(lat, 95), max: lat[lat.length - 1],
      mean: Math.round(lat.reduce((a, b) => a + b, 0) / lat.length)
    },
    observed_interblock_seconds: blockDeltas.length ? {
      n: blockDeltas.length, min: blockDeltas[0],
      median: pctile(blockDeltas, 50), max: blockDeltas[blockDeltas.length - 1]
    } : null,
    negative_security: {
      replay_rejected: replayRejected,
      zero_anchor_rejected: zeroRejected,
      unauthorized_submitter_rejected: unauthorizedRejected
    },
    first_block: rows[0].block_number,
    last_block: last.block_number,
    claim_boundary:
      "Public-testnet measurements under prevailing testnet load; execution gas " +
      "is consensus-independent EVM cost; inclusion latency is submit-to-first-" +
      "confirmation wall clock, not economic finality; results are not mainnet " +
      "or production performance claims.",
    timestamp_utc: new Date().toISOString(),
    commits_jsonl_sha256: crypto.createHash("sha256").update(fs.readFileSync(rowsPath)).digest("hex")
  };
  fs.writeFileSync(path.join(outDir, "summary.json"), JSON.stringify(summary, null, 2));
  console.log(`KPI_CONSENSUS_SUMMARY=${path.join(outDir, "summary.json")}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
