const fs = require("fs");
const path = require("path");
const { ethers, network } = require("hardhat");

async function main() {
  if (network.name !== "sepolia") {
    throw new Error("Run with --network sepolia");
  }

  const [admin] = await ethers.getSigners();
  const chainId = Number((await ethers.provider.getNetwork()).chainId);

  console.log(`KPI_SEPOLIA_CHAIN_ID=${chainId}`);
  console.log(`KPI_SEPOLIA_ADMIN=${admin.address}`);

  const balance = await ethers.provider.getBalance(admin.address);
  console.log(`KPI_SEPOLIA_ADMIN_BALANCE_WEI=${balance.toString()}`);

  const Ledger = await ethers.getContractFactory("Stage3AnomalyLedger");
  const ledger = await Ledger.deploy(admin.address);

  const deployTx = ledger.deploymentTransaction();
  const deployReceipt = await deployTx.wait();
  const ledgerAddress = await ledger.getAddress();

  console.log(`KPI_SEPOLIA_LEDGER_ADDRESS=${ledgerAddress}`);
  console.log(`KPI_SEPOLIA_DEPLOY_TX=${deployReceipt.hash}`);
  console.log(`KPI_SEPOLIA_DEPLOY_GAS=${deployReceipt.gasUsed.toString()}`);

  const now = Date.now();
  const commitment = ethers.keccak256(
    ethers.toUtf8Bytes(`stage4-sepolia-commitment-${now}`)
  );
  const evidenceHash = ethers.keccak256(
    ethers.toUtf8Bytes(`stage4-sepolia-evidence-${now}`)
  );

  const tx = await ledger.commit(commitment, evidenceHash);
  const receipt = await tx.wait();

  console.log(`KPI_SEPOLIA_COMMITMENT=${commitment}`);
  console.log(`KPI_SEPOLIA_EVIDENCE_HASH=${evidenceHash}`);
  console.log(`KPI_SEPOLIA_COMMIT_TX=${receipt.hash}`);
  console.log(`KPI_SEPOLIA_ANCHOR_GAS=${receipt.gasUsed.toString()}`);
  console.log(`KPI_SEPOLIA_BLOCK_NUMBER=${receipt.blockNumber}`);

  let replayRejected = false;
  try {
    await ledger.commit.staticCall(commitment, evidenceHash);
  } catch {
    replayRejected = true;
  }

  let zeroRejected = false;
  try {
    await ledger.commit.staticCall(ethers.ZeroHash, evidenceHash);
  } catch {
    zeroRejected = true;
  }

  const attacker = ethers.Wallet.createRandom().connect(ethers.provider);
  let unauthorizedRejected = false;
  try {
    await ledger.connect(attacker).commit.staticCall(
      ethers.keccak256(ethers.toUtf8Bytes("attacker-commitment")),
      evidenceHash
    );
  } catch {
    unauthorizedRejected = true;
  }

  console.log(`KPI_SEPOLIA_REPLAY_REJECTED=${replayRejected}`);
  console.log(`KPI_SEPOLIA_ZERO_ANCHOR_REJECTED=${zeroRejected}`);
  console.log(`KPI_SEPOLIA_UNAUTHORIZED_SUBMITTER_REJECTED=${unauthorizedRejected}`);

  const out = {
    network: "sepolia",
    chain_id: chainId,
    admin: admin.address,
    ledger_address: ledgerAddress,
    deploy_tx: deployReceipt.hash,
    deploy_gas: deployReceipt.gasUsed.toString(),
    commitment,
    evidence_hash: evidenceHash,
    commit_tx: receipt.hash,
    anchor_gas: receipt.gasUsed.toString(),
    block_number: receipt.blockNumber,
    replay_rejected: replayRejected,
    zero_anchor_rejected: zeroRejected,
    unauthorized_submitter_rejected: unauthorizedRejected,
    explorer_contract: `https://sepolia.etherscan.io/address/${ledgerAddress}`,
    explorer_commit_tx: `https://sepolia.etherscan.io/tx/${receipt.hash}`,
    timestamp: new Date().toISOString()
  };

  const outDir = path.join("artifacts", "l4", "stage4_sepolia");
  fs.mkdirSync(outDir, { recursive: true });

  fs.writeFileSync(
    path.join(outDir, "sepolia_stage3_anchor_evidence.json"),
    JSON.stringify(out, null, 2)
  );

  fs.writeFileSync(
    path.join(outDir, "sepolia_stage3_anchor_evidence.md"),
    [
      "# Stage 4 Sepolia Public-Testnet Anchor Evidence",
      "",
      `- Network: Sepolia`,
      `- Chain ID: ${chainId}`,
      `- Contract: ${ledgerAddress}`,
      `- Deploy tx: ${deployReceipt.hash}`,
      `- Commit tx: ${receipt.hash}`,
      `- Anchor gas: ${receipt.gasUsed.toString()}`,
      `- Block number: ${receipt.blockNumber}`,
      `- Replay rejected: ${replayRejected}`,
      `- Zero anchor rejected: ${zeroRejected}`,
      `- Unauthorized submitter rejected: ${unauthorizedRejected}`,
      `- Contract explorer: https://sepolia.etherscan.io/address/${ledgerAddress}`,
      `- Commit explorer: https://sepolia.etherscan.io/tx/${receipt.hash}`,
      ""
    ].join("\n")
  );

  console.log("[ok] wrote artifacts/l4/stage4_sepolia/sepolia_stage3_anchor_evidence.json");
  console.log("[ok] wrote artifacts/l4/stage4_sepolia/sepolia_stage3_anchor_evidence.md");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
