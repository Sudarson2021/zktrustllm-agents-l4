/*
 * Paired public-testnet benchmark for the Stage3AnomalyLedger audit anchor.
 *
 * The same compiled bytecode and matched commitments are submitted concurrently
 * to:
 *   - Ethereum Sepolia (Ethereum PoS protocol; permissioned test validator set)
 *   - IoTeX testnet (Randomized Delegated Proof of Stake / Roll-DPoS)
 *
 * This script records raw observations only. Paper-ready statistics are derived
 * by analyze_pos_rolldpos.py, which requires multiple sessions by default.
 *
 * Usage:
 *   REPEATS=30 WARMUPS=3 npx hardhat run --config hardhat.consensus.config.js \
 *     scripts/l4/consensus/run_paired_pos_rolldpos_benchmark.js
 */
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const hre = require("hardhat");

const { ethers } = hre;

const NETWORKS = {
  sepolia: {
    role: "pos",
    name: "Ethereum Sepolia",
    chainId: 11155111,
    consensus: "Ethereum PoS protocol (permissioned Sepolia validator set)",
    rpcEnv: "SEPOLIA_RPC_URL",
    privateKeyEnvs: ["SEPOLIA_PRIVATE_KEY", "DEPLOYER_PRIVATE_KEY"],
    explorer: "https://sepolia.etherscan.io"
  },
  iotex_testnet: {
    role: "roll_dpos",
    name: "IoTeX testnet",
    chainId: 4690,
    consensus: "IoTeX Randomized Delegated Proof of Stake (Roll-DPoS)",
    rpcEnv: "IOTEX_TESTNET_RPC_URL",
    defaultRpc: "https://babel-api.testnet.iotex.io",
    privateKeyEnvs: ["IOTEX_TESTNET_PRIVATE_KEY", "DEPLOYER_PRIVATE_KEY"],
    explorer: "https://testnet.iotexscan.io"
  }
};

function integerEnv(name, fallback, minimum, maximum) {
  const raw = process.env[name] || String(fallback);
  if (!/^\d+$/.test(raw)) {
    throw new Error(`${name} must be an integer; received ${JSON.stringify(raw)}`);
  }
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${name} must be in [${minimum}, ${maximum}]; received ${value}`);
  }
  return value;
}

function privateKeyFor(spec) {
  for (const name of spec.privateKeyEnvs) {
    const raw = process.env[name] || "";
    if (/^0x[0-9a-fA-F]{64}$/.test(raw)) return raw;
    if (/^[0-9a-fA-F]{64}$/.test(raw)) return `0x${raw}`;
  }
  throw new Error(
    `${spec.name}: set ${spec.privateKeyEnvs.join(" or ")} to a funded test-only key`
  );
}

function rpcFor(spec) {
  const value = process.env[spec.rpcEnv] || spec.defaultRpc || "";
  if (!/^https?:\/\//.test(value)) {
    throw new Error(`${spec.name}: set ${spec.rpcEnv} to an HTTP(S) JSON-RPC URL`);
  }
  return value;
}

function sanitizedRpcOrigin(value) {
  const parsed = new URL(value);
  return `${parsed.protocol}//${parsed.host}`;
}

function sha256Bytes(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function sha256File(filePath) {
  return sha256Bytes(fs.readFileSync(filePath));
}

function gitCommit() {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    }).trim();
  } catch {
    return null;
  }
}

function elapsedMs(startNs) {
  return Number(process.hrtime.bigint() - startNs) / 1e6;
}

function roundMs(value) {
  return Math.round(value * 1000) / 1000;
}

function receiptGasPrice(receipt, transaction) {
  const value = receipt.gasPrice ?? transaction.gasPrice ?? 0n;
  return value.toString();
}

async function safeClientVersion(provider) {
  try {
    return await provider.send("web3_clientVersion", []);
  } catch {
    return null;
  }
}

async function buildContext(key, spec) {
  const rpcUrl = rpcFor(spec);
  const provider = new ethers.JsonRpcProvider(rpcUrl, spec.chainId, {
    staticNetwork: true
  });
  const network = await provider.getNetwork();
  const actualChainId = Number(network.chainId);
  if (actualChainId !== spec.chainId) {
    throw new Error(
      `${spec.name}: expected chain ID ${spec.chainId}, received ${actualChainId}`
    );
  }

  const wallet = new ethers.Wallet(privateKeyFor(spec), provider);
  const balance = await provider.getBalance(wallet.address);
  if (balance === 0n) {
    throw new Error(
      `${spec.name}: ${wallet.address} has zero testnet balance; fund it before running`
    );
  }

  return {
    key,
    spec,
    provider,
    signer: wallet,
    rpcOrigin: sanitizedRpcOrigin(rpcUrl),
    clientVersion: await safeClientVersion(provider),
    startingBalanceWei: balance.toString()
  };
}

async function deployLedger(context, artifact) {
  const factory = new ethers.ContractFactory(
    artifact.abi,
    artifact.bytecode,
    context.signer
  );
  const startedAtUtc = new Date().toISOString();
  const startNs = process.hrtime.bigint();
  const contract = await factory.deploy(context.signer.address);
  const transaction = contract.deploymentTransaction();
  const receipt = await transaction.wait(1);
  const includedMs = roundMs(elapsedMs(startNs));
  const address = await contract.getAddress();
  const deployedCode = await context.provider.getCode(address);

  if (receipt.status !== 1) {
    throw new Error(`${context.spec.name}: contract deployment reverted`);
  }
  if (deployedCode === "0x") {
    throw new Error(`${context.spec.name}: deployment address contains no runtime code`);
  }

  return {
    contract,
    evidence: {
      started_at_utc: startedAtUtc,
      address,
      transaction_hash: receipt.hash,
      block_number: receipt.blockNumber,
      block_hash: receipt.blockHash,
      first_inclusion_latency_ms: includedMs,
      gas_used: receipt.gasUsed.toString(),
      effective_gas_price_wei: receiptGasPrice(receipt, transaction),
      deployed_code_keccak256: ethers.keccak256(deployedCode),
      explorer_url: `${context.spec.explorer}/address/${address}`
    }
  };
}

function findAnchorEvent(contract, receipt) {
  for (const log of receipt.logs) {
    try {
      const parsed = contract.interface.parseLog(log);
      if (parsed && parsed.name === "Stage3Anchored") return parsed;
    } catch {
      // Ignore unrelated logs.
    }
  }
  return null;
}

async function submitAnchor(context, contract, pairId, phase, commitment, evidenceHash) {
  const submittedAtUtc = new Date().toISOString();
  const startNs = process.hrtime.bigint();
  const transaction = await contract.commit(commitment, evidenceHash, {
    gasLimit: 120000n
  });
  const acceptedMs = roundMs(elapsedMs(startNs));
  const receipt = await transaction.wait(1);
  const includedMs = roundMs(elapsedMs(startNs));
  const block = await context.provider.getBlock(receipt.blockNumber);
  const anchorEvent = findAnchorEvent(contract, receipt);

  if (receipt.status !== 1) {
    throw new Error(`${context.spec.name}: ${pairId} reverted`);
  }
  if (!anchorEvent) {
    throw new Error(`${context.spec.name}: ${pairId} emitted no Stage3Anchored event`);
  }
  if (
    anchorEvent.args.commitment !== commitment ||
    anchorEvent.args.evidenceHash !== evidenceHash ||
    anchorEvent.args.submitter.toLowerCase() !== context.signer.address.toLowerCase()
  ) {
    throw new Error(`${context.spec.name}: ${pairId} event payload mismatch`);
  }

  return {
    network: context.key,
    pair_id: pairId,
    phase,
    submitted_at_utc: submittedAtUtc,
    transaction_hash: receipt.hash,
    explorer_url: `${context.spec.explorer}/tx/${receipt.hash}`,
    commitment,
    evidence_hash: evidenceHash,
    rpc_acceptance_latency_ms: acceptedMs,
    first_inclusion_latency_ms: includedMs,
    gas_used: receipt.gasUsed.toString(),
    effective_gas_price_wei: receiptGasPrice(receipt, transaction),
    block_number: receipt.blockNumber,
    block_hash: receipt.blockHash,
    block_timestamp_utc: block ? new Date(block.timestamp * 1000).toISOString() : null,
    receipt_status: receipt.status,
    anchor_event_verified: true
  };
}

async function matchedPair(contexts, contracts, sessionId, phase, index) {
  const pairId = `${sessionId}-${phase}-${String(index).padStart(3, "0")}`;
  const commitment = ethers.keccak256(
    ethers.toUtf8Bytes(`zktrustllm-consensus-commitment:${pairId}`)
  );
  const evidenceHash = ethers.keccak256(
    ethers.toUtf8Bytes(`zktrustllm-consensus-evidence:${pairId}`)
  );
  const [sepolia, iotex] = await Promise.all([
    submitAnchor(
      contexts.sepolia,
      contracts.sepolia,
      pairId,
      phase,
      commitment,
      evidenceHash
    ),
    submitAnchor(
      contexts.iotex_testnet,
      contracts.iotex_testnet,
      pairId,
      phase,
      commitment,
      evidenceHash
    )
  ]);
  return {
    pair_id: pairId,
    phase,
    matched_commitment: commitment,
    matched_evidence_hash: evidenceHash,
    observations: {
      sepolia,
      iotex_testnet: iotex
    }
  };
}

function extractRevertData(error) {
  return error?.data ?? error?.error?.data ?? error?.info?.error?.data ?? null;
}

async function rejectionProbe(label, expectedError, contract, callback) {
  try {
    await callback();
    return {
      label,
      rejected: false,
      expected_error: expectedError,
      expected_error_verified: false,
      rpc_method: "eth_call",
      error_code: null
    };
  } catch (error) {
    let actualError = error?.revert?.name ?? null;
    const revertData = extractRevertData(error);
    if (!actualError && revertData) {
      try {
        actualError = contract.interface.parseError(revertData)?.name ?? null;
      } catch {
        actualError = null;
      }
    }
    if (actualError !== expectedError) {
      throw new Error(
        `${label}: expected ${expectedError}, received ${actualError || "unparsed RPC error"}`
      );
    }
    return {
      label,
      rejected: true,
      expected_error: expectedError,
      actual_error: actualError,
      expected_error_verified: true,
      rpc_method: "eth_call",
      error_code: error && error.code ? String(error.code) : null
    };
  }
}

async function runSecurityProbes(context, contract, lastPair) {
  const previous = lastPair.observations[context.key];
  const probeEvidence = ethers.keccak256(
    ethers.toUtf8Bytes(`security-probe:${context.key}:${lastPair.pair_id}`)
  );
  const attacker = ethers.Wallet.createRandom().connect(context.provider);

  const replay = await rejectionProbe(
    "duplicate_commitment",
    "DuplicateCommitment",
    contract,
    () => contract.commit.staticCall(previous.commitment, probeEvidence)
  );
  const zero = await rejectionProbe(
    "zero_commitment",
    "ZeroCommitment",
    contract,
    () => contract.commit.staticCall(ethers.ZeroHash, probeEvidence)
  );
  const unauthorized = await rejectionProbe(
    "unauthorized_submitter",
    "AccessControlUnauthorizedAccount",
    contract,
    () => contract.connect(attacker).commit.staticCall(
      ethers.keccak256(
        ethers.toUtf8Bytes(`attacker:${context.key}:${lastPair.pair_id}`)
      ),
      probeEvidence
    )
  );

  return {
    method: "read-only eth_call against the deployed public-testnet contract state",
    replay,
    zero,
    unauthorized
  };
}

async function sampleRecentBlocks(context, sampleSize) {
  const latest = await context.provider.getBlockNumber();
  const first = Math.max(0, latest - sampleSize + 1);
  const blocks = [];
  for (let blockNumber = first; blockNumber <= latest; blockNumber += 1) {
    const block = await context.provider.getBlock(blockNumber);
    if (!block || block.number !== blockNumber) {
      throw new Error(`${context.spec.name}: could not fetch block ${blockNumber}`);
    }
    blocks.push({
      number: block.number,
      hash: block.hash,
      timestamp_utc: new Date(block.timestamp * 1000).toISOString(),
      timestamp_unix_s: block.timestamp
    });
  }
  return {
    sampling_rule: "consecutive block numbers ending at the post-run latest block",
    first_block: first,
    last_block: latest,
    blocks
  };
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

async function main() {
  const repeats = integerEnv("REPEATS", 30, 10, 500);
  const warmups = integerEnv("WARMUPS", 3, 0, 20);
  const blockSampleSize = integerEnv("BLOCK_SAMPLE_SIZE", 64, 20, 256);
  const startedAtUtc = new Date().toISOString();
  const stamp = startedAtUtc.replace(/[:.]/g, "-");
  const sessionId = process.env.SESSION_ID || stamp;
  if (!/^[A-Za-z0-9._-]+$/.test(sessionId)) {
    throw new Error("SESSION_ID may contain only letters, digits, dot, underscore, and hyphen");
  }

  const outRoot = process.env.CONSENSUS_OUT_DIR ||
    path.join("runtime_artifacts", "consensus_comparison");
  const outDir = path.join(outRoot, sessionId);
  if (fs.existsSync(outDir)) {
    throw new Error(`output directory already exists: ${outDir}`);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const artifact = await hre.artifacts.readArtifact("Stage3AnomalyLedger");
  const contractSource = path.join("contracts", "l4", "Stage3AnomalyLedger.sol");
  const scriptPath = path.join(
    "scripts",
    "l4",
    "consensus",
    "run_paired_pos_rolldpos_benchmark.js"
  );
  const artifactBytecodeKeccak = ethers.keccak256(artifact.bytecode);

  const [sepoliaContext, iotexContext] = await Promise.all([
    buildContext("sepolia", NETWORKS.sepolia),
    buildContext("iotex_testnet", NETWORKS.iotex_testnet)
  ]);
  const contexts = {
    sepolia: sepoliaContext,
    iotex_testnet: iotexContext
  };

  console.log(`KPI_CONSENSUS_SESSION_ID=${sessionId}`);
  console.log(`KPI_CONSENSUS_REPEATS=${repeats}`);
  console.log(`KPI_CONSENSUS_WARMUPS=${warmups}`);

  const [sepoliaDeployment, iotexDeployment] = await Promise.all([
    deployLedger(contexts.sepolia, artifact),
    deployLedger(contexts.iotex_testnet, artifact)
  ]);
  const contracts = {
    sepolia: sepoliaDeployment.contract,
    iotex_testnet: iotexDeployment.contract
  };

  if (
    sepoliaDeployment.evidence.deployed_code_keccak256 !==
    iotexDeployment.evidence.deployed_code_keccak256
  ) {
    throw new Error("deployed runtime bytecode differs between the two testnets");
  }

  const warmupPairs = [];
  for (let index = 0; index < warmups; index += 1) {
    warmupPairs.push(
      await matchedPair(contexts, contracts, sessionId, "warmup", index)
    );
  }

  const measuredPairs = [];
  for (let index = 0; index < repeats; index += 1) {
    const pair = await matchedPair(
      contexts,
      contracts,
      sessionId,
      "measurement",
      index
    );
    measuredPairs.push(pair);
    console.log(
      `KPI_CONSENSUS_PAIR=${index} ` +
      `SEPOLIA_MS=${pair.observations.sepolia.first_inclusion_latency_ms} ` +
      `IOTEX_MS=${pair.observations.iotex_testnet.first_inclusion_latency_ms}`
    );
  }

  const lastPair = measuredPairs[measuredPairs.length - 1];
  const [sepoliaSecurity, iotexSecurity, sepoliaBlocks, iotexBlocks] =
    await Promise.all([
      runSecurityProbes(contexts.sepolia, contracts.sepolia, lastPair),
      runSecurityProbes(contexts.iotex_testnet, contracts.iotex_testnet, lastPair),
      sampleRecentBlocks(contexts.sepolia, blockSampleSize),
      sampleRecentBlocks(contexts.iotex_testnet, blockSampleSize)
    ]);

  const finishedAtUtc = new Date().toISOString();
  const endingBalances = await Promise.all([
    contexts.sepolia.provider.getBalance(contexts.sepolia.signer.address),
    contexts.iotex_testnet.provider.getBalance(contexts.iotex_testnet.signer.address)
  ]);

  const benchmark = {
    schema: "zktrustllm.pos_rolldpos.paired_benchmark.v1",
    run_status: "completed",
    session_id: sessionId,
    started_at_utc: startedAtUtc,
    finished_at_utc: finishedAtUtc,
    git_commit: gitCommit(),
    design: {
      paired_concurrent_submission: true,
      repeats,
      warmups,
      confirmations_waited: 1,
      primary_metric: "client-observed submission-to-first-inclusion latency",
      latency_boundary:
        "Includes JSON-RPC/client overhead and public-testnet load; does not measure economic finality.",
      block_sampling: "consecutive post-run block headers",
      economic_cost_boundary:
        "Gas prices are recorded per network but native-token fees are not compared across assets."
    },
    implementation: {
      contract: "Stage3AnomalyLedger",
      contract_source: contractSource,
      contract_source_sha256: sha256File(contractSource),
      benchmark_script: scriptPath,
      benchmark_script_sha256: sha256File(scriptPath),
      artifact_bytecode_keccak256: artifactBytecodeKeccak,
      solidity: "0.8.20",
      optimizer_enabled: true,
      optimizer_runs: 200,
      via_ir: true
    },
    networks: {
      sepolia: {
        role: NETWORKS.sepolia.role,
        name: NETWORKS.sepolia.name,
        chain_id: NETWORKS.sepolia.chainId,
        consensus: NETWORKS.sepolia.consensus,
        rpc_origin: contexts.sepolia.rpcOrigin,
        rpc_client_version: contexts.sepolia.clientVersion,
        signer: contexts.sepolia.signer.address,
        starting_balance_wei: contexts.sepolia.startingBalanceWei,
        ending_balance_wei: endingBalances[0].toString(),
        deployment: sepoliaDeployment.evidence,
        security_probes: sepoliaSecurity,
        block_sample: sepoliaBlocks
      },
      iotex_testnet: {
        role: NETWORKS.iotex_testnet.role,
        name: NETWORKS.iotex_testnet.name,
        chain_id: NETWORKS.iotex_testnet.chainId,
        consensus: NETWORKS.iotex_testnet.consensus,
        rpc_origin: contexts.iotex_testnet.rpcOrigin,
        rpc_client_version: contexts.iotex_testnet.clientVersion,
        signer: contexts.iotex_testnet.signer.address,
        starting_balance_wei: contexts.iotex_testnet.startingBalanceWei,
        ending_balance_wei: endingBalances[1].toString(),
        deployment: iotexDeployment.evidence,
        security_probes: iotexSecurity,
        block_sample: iotexBlocks
      }
    },
    warmup_pairs: warmupPairs,
    measured_pairs: measuredPairs,
    claim_boundary:
      "Public-testnet, client-observed first-inclusion measurements for one isolated EVM audit-anchor micro-benchmark. Sepolia has a permissioned test validator set. Results do not establish mainnet throughput, economic finality, decentralization, or production O-RAN performance."
  };

  const benchmarkPath = path.join(outDir, "benchmark.json");
  writeJson(benchmarkPath, benchmark);
  const digest = sha256File(benchmarkPath);
  fs.writeFileSync(
    path.join(outDir, "SHA256SUMS.txt"),
    `${digest}  benchmark.json\n`
  );

  console.log(`KPI_CONSENSUS_BENCHMARK=${benchmarkPath}`);
  console.log(`KPI_CONSENSUS_BENCHMARK_SHA256=${digest}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
