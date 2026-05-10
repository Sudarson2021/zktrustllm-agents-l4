# Step 109 Persistent Local Hardhat Audit-Anchor Validation

## Purpose

Step 109 validates the Level 4 automation audit-anchor registry against a persistent local Hardhat JSON-RPC node.

This extends Steps 103-105 by moving from isolated ephemeral Hardhat execution to a long-running local blockchain process.

## Workflow

The Step 109 runner performs:

1. Checks whether a local JSON-RPC endpoint is already reachable at `127.0.0.1:8545`.
2. Starts `npx hardhat node` if no local node is running.
3. Compiles the smart contracts.
4. Deploys `L4AutomationAuditAnchorRegistry`.
5. Reads the Step 102 blockchain-ready audit-anchor payload.
6. Submits the audit anchor to the local registry.
7. Validates the stored ledger hash, ledger file hash, IPFS CID, and commitment hash.
8. Runs negative-security checks for duplicate replay and zero commitment.
9. Writes JSON and Markdown evidence.

## Research Meaning

This step strengthens the trust-plane evaluation because it validates the audit-anchor workflow against a persistent local blockchain process.

The project now demonstrates a more realistic blockchain validation environment while remaining safe, local, reproducible, and approval-gated.

## Safety Boundary

This step uses local Hardhat only.

It does not:

- deploy to a public blockchain,
- spend real funds,
- push code,
- modify Git history,
- email supervisors,
- submit papers,
- delete prior evidence.

## Main Artifacts

- Runner:
  - `scripts/l4/run_step109_persistent_hardhat_anchor_validation.sh`

- Validation script:
  - `scripts/l4/validate_l4_audit_anchor_persistent_hardhat.js`

- Result JSON:
  - `results/l4_persistent_hardhat_anchor/persistent_hardhat_anchor_result.json`

- Result Markdown:
  - `results/l4_persistent_hardhat_anchor/persistent_hardhat_anchor_result.md`
