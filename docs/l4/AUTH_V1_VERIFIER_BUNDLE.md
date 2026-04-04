# AUTH_V1 Verifier Bundle

## Purpose
This note defines the stable bundle interface between:
- prover-side artifacts
- proof artifacts
- on-chain verifier submission

## Builder
- `scripts/l4/build_auth_v1_prover_bundle.py`

## Outputs
- `artifacts/out_l4/prover_bundle.auth_v1.json`
- `artifacts/out_l4/verifier_bundle.auth_v1.json`

## Prover bundle
The prover bundle is the canonical handoff object for future prover implementations.

It includes:
- public inputs in raw hex and field-decimal form
- private witness placeholders in raw hex and field-decimal form
- derived digests
- runtime metadata
- current proof artifact

## Verifier bundle
The verifier bundle is the canonical handoff object for future on-chain submission tooling.

It includes:
- target contract address
- submission method name
- ordered submission arguments
- proof blob
- proof digest
- trace and task metadata

## Current status
At the current prototype stage:
- the prover bundle is pre-Groth16
- the verifier bundle targets the current `DecisionAttestorZKV2` path
- the proof blob is still produced by the mock proof stub

## Future replacement path
Later, the internals of the proof artifact can change, while preserving:
- the bundle schemas
- public input order
- contract submission order
- runtime metadata fields

This is intentional so that future prover integration does not require redesigning the full workflow.
