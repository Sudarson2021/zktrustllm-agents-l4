# Known Artifact Limitation: ReputationManager Legacy Test

The previous full-suite blocker came from `test/reputation.test.js`, which called `rep.setWeights`. The current `ReputationManager` ABI no longer exposes this function, so the test is stale relative to the current contract implementation.

This issue is unrelated to the AuthV2.2 RBAC rescue pass and unrelated to the core ZKTrustLLM-Agents L4 trust-plane novelty. For artifact review, the stale legacy test should either be updated to match the current ABI or retained as a skipped legacy test with this explanation.

The publication-target security evidence is anchored on:
- `DecisionAttestorAuthV2_2`
- `SUBMITTER_ROLE`
- unauthorized submitter rejection
- Groth16/BN254 verifier deployment path
- ablation manifests
- publication evidence summary
