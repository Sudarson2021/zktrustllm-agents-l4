const fs = require("fs");
const path = require("path");

async function main() {
  const hre = require("hardhat");
  const { ethers } = hre;

  const root = process.cwd();
  const anchorPath = path.join(root, "results/l4_audit_anchor/audit_ledger_blockchain_ready_anchor.json");
  const outDir = path.join(root, "results/l4_onchain_anchor");

  fs.mkdirSync(outDir, { recursive: true });

  if (!fs.existsSync(anchorPath)) {
    throw new Error(`Missing anchor payload: ${anchorPath}`);
  }

  const payload = JSON.parse(fs.readFileSync(anchorPath, "utf8"));

  function asBytes32(value, name) {
    if (!value || typeof value !== "string") {
      throw new Error(`Missing ${name}`);
    }
    const clean = value.startsWith("0x") ? value.slice(2) : value;
    if (!/^[0-9a-fA-F]{64}$/.test(clean)) {
      throw new Error(`${name} must be 32-byte hex`);
    }
    return "0x" + clean;
  }

  const ledgerHash = asBytes32(payload.ledgerHash, "ledgerHash");
  const ledgerSha256 = asBytes32(payload.ledgerSha256, "ledgerSha256");
  const anchorCommitmentHash = asBytes32(payload.anchorCommitmentHash, "anchorCommitmentHash");
  const ipfsCid = payload.ipfsCid || "";
  const anchorType = payload.anchorType || "ZKTrustLLM_L4_AUTOMATION_AUDIT_LEDGER_ANCHOR";

  const Registry = await ethers.getContractFactory("L4AutomationAuditAnchorRegistry");
  const registry = await Registry.deploy();

  if (registry.waitForDeployment) {
    await registry.waitForDeployment();
  } else {
    await registry.deployed();
  }

  const registryAddress = registry.target || registry.address;

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

  const result = {
    experiment: "step103_onchain_audit_anchor_registry",
    network: hre.network.name,
    registryAddress,
    submitter: receipt.from,
    transactionHash: receipt.hash || receipt.transactionHash,
    blockNumber: receipt.blockNumber,
    gasUsed: receipt.gasUsed ? receipt.gasUsed.toString() : null,
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
      timestamp: stored.timestamp ? stored.timestamp.toString() : null,
      submitter: stored.submitter
    },
    validation: {
      commitmentMatches: stored.anchorCommitmentHash.toLowerCase() === anchorCommitmentHash.toLowerCase(),
      ledgerHashMatches: stored.ledgerHash.toLowerCase() === ledgerHash.toLowerCase(),
      ledgerSha256Matches: stored.ledgerSha256.toLowerCase() === ledgerSha256.toLowerCase(),
      ipfsCidMatches: stored.ipfsCid === ipfsCid
    }
  };

  fs.writeFileSync(
    path.join(outDir, "onchain_audit_anchor_result.json"),
    JSON.stringify(result, null, 2)
  );

  const md = `# Step 103 On-Chain Audit Anchor Registry

## Purpose

This step submits the Step 102 IPFS/blockchain-ready audit anchor to a local Hardhat smart contract registry.

## Result

- Network: \`${result.network}\`
- Registry address: \`${result.registryAddress}\`
- Transaction hash: \`${result.transactionHash}\`
- Block number: \`${result.blockNumber}\`
- Gas used: \`${result.gasUsed}\`
- Anchor ID: \`${result.anchorId}\`
- IPFS CID: \`${ipfsCid}\`
- Anchor commitment hash: \`${anchorCommitmentHash}\`

## Validation

| Check | Result |
|---|---:|
| Commitment matches | ${result.validation.commitmentMatches} |
| Ledger hash matches | ${result.validation.ledgerHashMatches} |
| Ledger SHA-256 matches | ${result.validation.ledgerSha256Matches} |
| IPFS CID matches | ${result.validation.ipfsCidMatches} |

## Research Meaning

Step 103 closes the loop from agentic automation evidence to a smart-contract-verifiable audit anchor.

The L4 workflow now has: automated experiment execution, KPI decisioning, policy-gated remediation, hash-chained audit evidence, IPFS anchoring, and local on-chain registry validation.
`;

  fs.writeFileSync(
    path.join(outDir, "onchain_audit_anchor_result.md"),
    md
  );

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
