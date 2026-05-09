# Step 104 On-Chain Anchor Negative-Security Validation

## Purpose

This step validates replay protection and invalid-anchor rejection for the L4 audit-anchor registry.

## Result

- Network: `hardhat`
- Registry address: `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- Overall status: **PASS**
- Anchor count after tests: `1`

## Positive Control

| Item | Value |
|---|---|
| Valid transaction hash | `0x3aa06732baa252f303eb24a6b20c118a6a3c665b7e8cbcb6dce0a2b9d3053277` |
| Block number | `2` |
| Gas used | `320095` |

## Negative Tests

| Test | Rejected | Meaning |
|---|---:|---|
| Duplicate commitment replay | true | Prevents the same audit commitment being anchored twice |
| Zero commitment | true | Prevents empty/invalid commitment anchors |

## Validation Checks

| Check | Result |
|---|---:|
| Valid anchor stored | true |
| Duplicate replay rejected | true |
| Zero commitment rejected | true |
| Commitment still matches | true |
| Ledger hash still matches | true |
| Ledger SHA-256 still matches | true |
| IPFS CID still matches | true |

## Research Meaning

Step 104 strengthens the trust-plane evaluation by showing that the on-chain audit-anchor registry does not merely store evidence, but also enforces basic security constraints.

The registry rejects duplicate audit commitments and empty commitments. This supports the Level 4 claim that agentic automation evidence can be anchored in a replay-resistant blockchain registry.

## Boundary

The smart contract enforces non-zero commitments and replay protection. It does not independently recompute IPFS or ledger commitments on-chain. The CID-ledger binding is validated off-chain by the Step 102 canonical commitment payload.
