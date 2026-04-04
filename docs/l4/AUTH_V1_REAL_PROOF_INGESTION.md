# AUTH_V1 Real Proof Ingestion

## Purpose
This note defines the ingestion path from a real ZoKrates-generated proof into the stable repository artifact workflow.

## Scripts
Real proof builder:
- `scripts/l4/build_auth_v1_real_proof_from_zokrates.py`

Real verifier bundle builder:
- `scripts/l4/build_auth_v1_real_verifier_bundle.py`

Submission preflight:
- `scripts/l4/submit_auth_v1_real_verifier_bundle.py`

## Source artifact
The ingestion path starts from:
- `artifacts/out_l4/zokrates_docker/proof.json`

## Stable repo artifacts created
- `artifacts/out_l4/proof_output.auth_v1.real.json`
- `artifacts/out_l4/verifier_bundle.auth_v1.real.json`
- `artifacts/out_l4/submission_preflight.auth_v1.real.json`

## Important finding
The ZoKrates `inputs` array contains field elements reduced modulo the BN128 scalar field.
So these values differ from the original raw 32-byte public input hashes, but they are the correct proving-system representation.

## Current status
The real proof is now ingestible into the repository workflow.

However, the currently deployed `DecisionAttestorZK` path is still tied to the mock digest-style verifier and is therefore not yet able to verify real Groth16 proof points.

## What is ready now
- real proof generation
- real proof ingestion
- real verifier bundle generation
- honest preflight status for submission

## Next required deployment step
Deploy a Groth16-capable verifier/wrapper path and then wire the real verifier bundle into that contract.
