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

async function main() {
  const hre = require("hardhat");
  const { ethers } = hre;

  const root = process.cwd();
  const anchorPath = path.join(root, "results/l4_audit_anchor/audit_ledger_blockchain_ready_anchor.json");
  const outDir = path.join(root, "results/l4_onchain_anchor_negative");

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

  const validTx = await registry.submitAnchor(
    ledgerHash,
    ledgerSha256,
    anchorCommitmentHash,
    ipfsCid,
    anchorType
  );

  const validReceipt = await validTx.wait();

  const duplicateResult = await expectRevert("duplicate_commitment_replay", async () => {
    const tx = await registry.submitAnchor(
      ledgerHash,
      ledgerSha256,
      anchorCommitmentHash,
      ipfsCid,
      anchorType
    );
    await tx.wait();
  });

  const zeroCommitmentResult = await expectRevert("zero_commitment", async () => {
    const tx = await registry.submitAnchor(
      ledgerHash,
      ledgerSha256,
      "0x0000000000000000000000000000000000000000000000000000000000000000",
      ipfsCid,
      anchorType
    );
    await tx.wait();
  });

  const anchorCount = Number(await registry.anchorCount());
  const stored = await registry.getAnchor(0);

  const validations = {
    validAnchorStored: anchorCount === 1,
    duplicateReplayRejected: duplicateResult.rejected,
    zeroCommitmentRejected: zeroCommitmentResult.rejected,
    commitmentStillMatches: stored.anchorCommitmentHash.toLowerCase() === anchorCommitmentHash.toLowerCase(),
    ledgerHashStillMatches: stored.ledgerHash.toLowerCase() === ledgerHash.toLowerCase(),
    ledgerSha256StillMatches: stored.ledgerSha256.toLowerCase() === ledgerSha256.toLowerCase(),
    ipfsCidStillMatches: stored.ipfsCid === ipfsCid
  };

  const overallPass = Object.values(validations).every(Boolean);

  const result = {
    experiment: "step104_onchain_anchor_negative_security",
    network: hre.network.name,
    registryAddress,
    validSubmission: {
      transactionHash: validReceipt.hash || validReceipt.transactionHash,
      blockNumber: validReceipt.blockNumber,
      gasUsed: validReceipt.gasUsed ? validReceipt.gasUsed.toString() : null
    },
    negativeTests: {
      duplicateCommitmentReplay: duplicateResult,
      zeroCommitment: zeroCommitmentResult
    },
    anchorCount,
    storedAnchor: {
      ledgerHash: stored.ledgerHash,
      ledgerSha256: stored.ledgerSha256,
      anchorCommitmentHash: stored.anchorCommitmentHash,
      ipfsCid: stored.ipfsCid,
      anchorType: stored.anchorType,
      timestamp: stored.timestamp ? stored.timestamp.toString() : null,
      submitter: stored.submitter
    },
    validations,
    overallStatus: overallPass ? "PASS" : "FAIL",
    boundary: "The contract enforces non-zero commitments and replay protection. Semantic validation of CID-ledger binding remains off-chain via the Step 102 commitment payload."
  };

  fs.writeFileSync(
    path.join(outDir, "onchain_anchor_negative_security_result.json"),
    JSON.stringify(result, null, 2)
  );

  const md = `# Step 104 On-Chain Anchor Negative-Security Validation

## Purpose

This step validates replay protection and invalid-anchor rejection for the L4 audit-anchor registry.

## Result

- Network: \`${result.network}\`
- Registry address: \`${registryAddress}\`
- Overall status: **${result.overallStatus}**
- Anchor count after tests: \`${anchorCount}\`

## Positive Control

| Item | Value |
|---|---|
| Valid transaction hash | \`${result.validSubmission.transactionHash}\` |
| Block number | \`${result.validSubmission.blockNumber}\` |
| Gas used | \`${result.validSubmission.gasUsed}\` |

## Negative Tests

| Test | Rejected | Meaning |
|---|---:|---|
| Duplicate commitment replay | ${duplicateResult.rejected} | Prevents the same audit commitment being anchored twice |
| Zero commitment | ${zeroCommitmentResult.rejected} | Prevents empty/invalid commitment anchors |

## Validation Checks

| Check | Result |
|---|---:|
| Valid anchor stored | ${validations.validAnchorStored} |
| Duplicate replay rejected | ${validations.duplicateReplayRejected} |
| Zero commitment rejected | ${validations.zeroCommitmentRejected} |
| Commitment still matches | ${validations.commitmentStillMatches} |
| Ledger hash still matches | ${validations.ledgerHashStillMatches} |
| Ledger SHA-256 still matches | ${validations.ledgerSha256StillMatches} |
| IPFS CID still matches | ${validations.ipfsCidStillMatches} |

## Research Meaning

Step 104 strengthens the trust-plane evaluation by showing that the on-chain audit-anchor registry does not merely store evidence, but also enforces basic security constraints.

The registry rejects duplicate audit commitments and empty commitments. This supports the Level 4 claim that agentic automation evidence can be anchored in a replay-resistant blockchain registry.

## Boundary

The smart contract enforces non-zero commitments and replay protection. It does not independently recompute IPFS or ledger commitments on-chain. The CID-ledger binding is validated off-chain by the Step 102 canonical commitment payload.
`;

  fs.writeFileSync(
    path.join(outDir, "onchain_anchor_negative_security_result.md"),
    md
  );

  console.log(JSON.stringify(result, null, 2));

  if (!overallPass) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
