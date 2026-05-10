# Step 104 On-Chain Anchor Negative-Security Validation

## Purpose

Step 104 validates replay protection and invalid-anchor rejection for the Level 4 automation audit-anchor registry.

This extends Step 103 by testing not only successful anchor submission, but also failure behaviour.

## Tested Security Properties

The experiment validates:

- valid audit anchor can be stored,
- duplicate `anchorCommitmentHash` replay is rejected,
- zero commitment is rejected,
- previously stored valid anchor remains unchanged after failed negative tests.

## Smart Contract Under Test

- `contracts/l4/L4AutomationAuditAnchorRegistry.sol`

## Test Script

- `scripts/l4/test_l4_audit_anchor_registry_negative_security.js`

## Result Artifacts

- `results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json`
- `results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.md`

## Research Meaning

Step 104 strengthens the trust-plane contribution of the project.

The L4 automation evidence chain is now not only anchored on-chain, but also protected against basic replay and empty-commitment misuse.

This helps position the project as a proof-governed and audit-governed agentic AI automation system for secure 5G/O-RAN edge workflows.

## Boundary

The registry verifies replay and non-zero commitment constraints.

Semantic validation of the relationship between IPFS CID, ledger hash, and commitment hash remains off-chain through the Step 102 canonical commitment payload.
