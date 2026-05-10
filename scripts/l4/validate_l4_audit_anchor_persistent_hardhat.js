const fs = require("fs");
const path = require("path");

async function expectRevert(label, fn) {
  try {
    await fn();
    return {
      label,
      rejected: false,
      error: null
    };
  } catch (err) {
    return {
      label,
      rejected: true,
      error: err.message || String(err)
    };
  }
}

function writeMarkdown(outPath, result) {
  const lines = [];

  lines.push("# Step 109 Persistent Local Hardhat Audit-Anchor Validation");
  lines.push("");
  lines.push("## Purpose");
  lines.push("");
  lines.push("This step validates the L4 automation audit-anchor registry against a persistent local Hardhat node.");
  lines.push("");
  lines.push("Unlike earlier ephemeral Hardhat runs, this test starts or uses a local JSON-RPC node, deploys the registry, submits the Step 102 audit anchor, and then validates replay and invalid-commitment rejection.");
  lines.push("");
  lines.push("## Result");
  lines.push("");
  lines.push(`- Network: \`${result.network}\``);
  lines.push(`- Chain ID: \`${result.chainId}\``);
  lines.push(`- RPC URL: \`${result.rpcUrl}\``);
  lines.push(`- Registry address: \`${result.registryAddress}\``);
  lines.push(`- Submitter: \`${result.submitter}\``);
  lines.push(`- Transaction hash: \`${result.validSubmission.transactionHash}\``);
  lines.push(`- Block number: \`${result.validSubmission.blockNumber}\``);
  lines.push(`- Gas used: \`${result.validSubmission.gasUsed}\``);
  lines.push(`- Anchor ID: \`${result.anchorId}\``);
  lines.push(`- Overall status: **${result.overallStatus}**`);
  lines.push("");
  lines.push("## Anchor Evidence");
  lines.push("");
  lines.push("| Evidence | Value |");
  lines.push("|---|---|");
  lines.push(`| Ledger hash | \`${result.input.ledgerHash}\` |`);
  lines.push(`| Ledger SHA-256 | \`${result.input.ledgerSha256}\` |`);
  lines.push(`| Anchor commitment hash | \`${result.input.anchorCommitmentHash}\` |`);
  lines.push(`| IPFS CID | \`${result.input.ipfsCid}\` |`);
  lines.push(`| Anchor type | \`${result.input.anchorType}\` |`);
  lines.push("");
  lines.push("## Negative-Security Tests");
  lines.push("");
  lines.push("| Test | Rejected | Meaning |");
  lines.push("|---|---:|---|");
  lines.push(`| Duplicate commitment replay | ${result.negativeTests.duplicateCommitmentReplay.rejected} | Prevents the same audit commitment being anchored twice |`);
  lines.push(`| Zero commitment | ${result.negativeTests.zeroCommitment.rejected} | Prevents empty audit commitments |`);
  lines.push("");
  lines.push("## Validation Checks");
  lines.push("");
  lines.push("| Check | Result |");
  lines.push("|---|---:|");
  for (const [key, value] of Object.entries(result.validations)) {
    lines.push(`| ${key} | ${value} |`);
  }
  lines.push("");
  lines.push("## Research Meaning");
  lines.push("");
  lines.push("Step 109 strengthens the trust-plane evaluation by moving audit-anchor validation from isolated ephemeral Hardhat runs to a persistent local blockchain process.");
  lines.push("");
  lines.push("This is closer to a realistic long-running blockchain validation environment while remaining safe, local, repeatable, and free from public-chain deployment risk.");
  lines.push("");
  lines.push("## Safety Boundary");
  lines.push("");
  lines.push("This step uses only a local Hardhat JSON-RPC node. It does not deploy to a public chain, spend real funds, push code, submit papers, or modify Git history.");
  lines.push("");

  fs.writeFileSync(outPath, lines.join("\n"));
}

async function main() {
  const hre = require("hardhat");
  const { ethers } = hre;

  const root = process.cwd();
  const outDir = path.join(root, "results/l4_persistent_hardhat_anchor");
  fs.mkdirSync(outDir, { recursive: true });

  const anchorPath = path.join(root, "results/l4_audit_anchor/audit_ledger_blockchain_ready_anchor.json");
  const resultJsonPath = path.join(outDir, "persistent_hardhat_anchor_result.json");
  const resultMdPath = path.join(outDir, "persistent_hardhat_anchor_result.md");

  if (!fs.existsSync(anchorPath)) {
    throw new Error(`Missing Step 102 anchor payload: ${anchorPath}`);
  }

  const payload = JSON.parse(fs.readFileSync(anchorPath, "utf8"));

  function asBytes32(value, name) {
    if (!value || typeof value !== "string") {
      throw new Error(`Missing ${name}`);
    }

    const clean = value.startsWith("0x") ? value.slice(2) : value;

    if (!/^[0-9a-fA-F]{64}$/.test(clean)) {
      throw new Error(`${name} must be 32 bytes / 64 hex chars`);
    }

    return "0x" + clean.toLowerCase();
  }

  const ledgerHash = asBytes32(payload.ledgerHash, "ledgerHash");
  const ledgerSha256 = asBytes32(payload.ledgerSha256, "ledgerSha256");
  const anchorCommitmentHash = asBytes32(payload.anchorCommitmentHash, "anchorCommitmentHash");
  const ipfsCid = payload.ipfsCid || "";
  const anchorType = payload.anchorType || "ZKTrustLLM_L4_AUTOMATION_AUDIT_LEDGER_ANCHOR";

  const [submitter] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();

  const Registry = await ethers.getContractFactory("L4AutomationAuditAnchorRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();

  const registryAddress = await registry.getAddress();

  const tx = await registry.submitAnchor(
    ledgerHash,
    ledgerSha256,
    anchorCommitmentHash,
    ipfsCid,
    anchorType
  );

  const receipt = await tx.wait();

  const anchorCount = await registry.anchorCount();
  const anchorId = Number(anchorCount) - 1;
  const stored = await registry.getAnchor(anchorId);

  const duplicateCommitmentReplay = await expectRevert(
    "duplicate_commitment_replay",
    async () => {
      const replayTx = await registry.submitAnchor(
        ledgerHash,
        ledgerSha256,
        anchorCommitmentHash,
        ipfsCid,
        anchorType
      );
      await replayTx.wait();
    }
  );

  const zeroCommitment = await expectRevert(
    "zero_commitment",
    async () => {
      const zeroTx = await registry.submitAnchor(
        ledgerHash,
        ledgerSha256,
        "0x" + "0".repeat(64),
        ipfsCid,
        anchorType
      );
      await zeroTx.wait();
    }
  );

  const validations = {
    commitmentMatches: String(stored.anchorCommitmentHash).toLowerCase() === anchorCommitmentHash.toLowerCase(),
    ledgerHashMatches: String(stored.ledgerHash).toLowerCase() === ledgerHash.toLowerCase(),
    ledgerSha256Matches: String(stored.ledgerSha256).toLowerCase() === ledgerSha256.toLowerCase(),
    ipfsCidMatches: stored.ipfsCid === ipfsCid,
    duplicateReplayRejected: duplicateCommitmentReplay.rejected === true,
    zeroCommitmentRejected: zeroCommitment.rejected === true,
    anchorCountIsOne: Number(await registry.anchorCount()) === 1
  };

  const overallStatus = Object.values(validations).every(Boolean) ? "PASS" : "FAIL";

  const result = {
    experiment: "step109_persistent_hardhat_audit_anchor_validation",
    createdAt: new Date().toISOString(),
    network: hre.network.name,
    chainId: network.chainId.toString(),
    rpcUrl: process.env.L4_HARDHAT_RPC_URL || "http://127.0.0.1:8545",
    registryAddress,
    submitter: submitter.address,
    validSubmission: {
      transactionHash: receipt.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString()
    },
    anchorId,
    input: {
      ledgerHash,
      ledgerSha256,
      anchorCommitmentHash,
      ipfsCid,
      anchorType
    },
    stored: {
      ledgerHash: stored.ledgerHash,
      ledgerSha256: stored.ledgerSha256,
      anchorCommitmentHash: stored.anchorCommitmentHash,
      ipfsCid: stored.ipfsCid,
      anchorType: stored.anchorType,
      timestamp: stored.timestamp.toString(),
      submitter: stored.submitter
    },
    negativeTests: {
      duplicateCommitmentReplay,
      zeroCommitment
    },
    validations,
    overallStatus,
    boundary: "Persistent local Hardhat only. No public-chain deployment or real funds."
  };

  fs.writeFileSync(resultJsonPath, JSON.stringify(result, null, 2));
  writeMarkdown(resultMdPath, result);

  console.log(JSON.stringify({
    experiment: result.experiment,
    overallStatus,
    network: result.network,
    chainId: result.chainId,
    registryAddress,
    transactionHash: receipt.hash,
    gasUsed: receipt.gasUsed.toString(),
    resultJson: "results/l4_persistent_hardhat_anchor/persistent_hardhat_anchor_result.json",
    resultMarkdown: "results/l4_persistent_hardhat_anchor/persistent_hardhat_anchor_result.md"
  }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
