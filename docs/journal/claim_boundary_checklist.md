# ZKTrustLLM-Agents L4 Claim Boundary Checklist

## Current status

This checklist is updated after the `l4-testnet-and-frozen-proof-evidence` branch added Sepolia AuthV2.2 deployment evidence and frozen proof artifacts.

## Safe claims

The manuscript may claim:

- Local Hardhat validation is available.
- AuthV2.2 RBAC is implemented.
- `submitDecision(...)` is restricted by `onlyRole(SUBMITTER_ROLE)`.
- Unauthorized submitters are rejected.
- AuthV2.2 targeted authorization tests pass 3/3.
- 20/20 repeated local authorization-test runs pass.
- Local Hardhat gas evidence is available for `DecisionAttestorAuthV2_2`, `AuthV2_2Verifier`, and `grantRole`.
- Public Sepolia testnet deployment evidence is available for the AuthV2.2 verifier and RBAC-controlled AuthV2.2 attestor.
- Frozen AuthV2.2 proof artifacts are available under `runtime_artifacts/l4/auth_v2_2/`.
- The positive frozen proof verifies successfully in ZoKrates.
- The mutated negative proof fails verification as expected.

## Claims still NOT allowed

The manuscript must not claim:

- Ethereum mainnet deployment.
- Polygon Amoy deployment unless separate evidence is added.
- Production MNO/O-RAN deployment.
- Etherscan/Polygonscan source-code verification unless contract verification artifacts are added.
- Full end-to-end O-RAN testbed deployment.
- Live packet-capture media KPI measurement unless tshark/VLC/tc/netem/O-RAN telemetry logs are added.
- Complete full-ZK prover-time coverage for all 240 evaluation records unless direct prover logs are collected.
- Complete policy-matrix or threat-matrix formal verification beyond the implemented tests and current TLA+ preparation artifacts.

## Correct wording

"The current artifact reports local Hardhat validation plus public Sepolia testnet evidence for the AuthV2.2 verifier and RBAC-controlled attestor, together with frozen AuthV2.2 proof artifacts. The evidence supports reproducible trust-plane validation and negative-proof checking, but does not claim production deployment, Ethereum mainnet performance, full packet-capture media measurement, or complete end-to-end O-RAN testbed deployment."
