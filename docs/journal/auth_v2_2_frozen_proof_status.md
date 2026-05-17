# AuthV2.2 Frozen Proof Status

Current status:
- AuthV2.2 verifier deployment path exists.
- Groth16/BN254 verifier lineage is present.
- AuthV2.2 RBAC tests pass locally.
- Frozen AuthV2.2 positive and negative proof payloads are not yet generated.

Claim boundary:
The manuscript may claim Groth16-compatible AuthV2.2 verifier support and local verifier deployment evidence, but it must not claim frozen AuthV2.2 proof reproducibility until `runtime_artifacts/l4/auth_v2_2/proof.frozen.json`, `proof.bad.json`, and `proof_payload.auth_v2_2.frozen.json` exist.
