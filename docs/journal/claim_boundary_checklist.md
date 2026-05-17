# ZKTrustLLM-Agents L4 Claim Boundary Checklist

## Safe claims

The manuscript may claim:

- Local Hardhat validation only.
- AuthV2.2 RBAC is implemented.
- `submitDecision(...)` is restricted by `onlyRole(SUBMITTER_ROLE)`.
- Unauthorized submitters are rejected.
- AuthV2.2 targeted authorization tests pass 3/3.
- 20/20 repeated local authorization-test runs pass.
- Local Hardhat gas evidence is available for:
  - `DecisionAttestorAuthV2_2` deployment,
  - `AuthV2_2Verifier` deployment,
  - `grantRole`.
- Groth16/BN254 verifier lineage exists.
- AuthV2.2 verifier deployment path exists.
- Ablation manifests exist.

## Claims NOT allowed yet

The manuscript must not claim:

- Public testnet deployment.
- Sepolia deployment.
- Polygon Amoy deployment.
- Etherscan/Polygonscan verified deployment.
- Public-chain transaction evidence.
- Frozen AuthV2.2 proof payloads generated.
- Completed AuthV2.2 ZK proof reproducibility.
- End-to-end ablation reruns.
- Production deployment.

## Correct wording

Use:

"The current artifact reports local Hardhat validation only. Public testnet deployment and frozen AuthV2.2 proof payload generation are reserved as next milestones and are not claimed as completed results."
