# AUTH_V1 Prover Adapter

## Purpose
This note defines the stable adapter layer between the current repository workflow and a future real proving toolchain for `auth_v1`.

## Builder
- `scripts/l4/build_auth_v1_real_prover_adapter.py`

## Validator
- `scripts/l4/validate_auth_v1_real_prover_adapter.py`

## Artifact
- `artifacts/out_l4/prover_adapter.auth_v1.json`

## Why this exists
The adapter artifact captures:
- the fixed circuit field order
- the current witness export
- the expected future real-proof artifact shape
- the verifier target
- the submission method and argument shape

This allows the proving toolchain to be integrated later without changing the overall L4 workflow.

## Stable parts
The following should remain stable:
- public input order
- private witness order
- witness export field names
- verifier bundle submission method
- runtime metadata and trace/task binding

## Future replacement
Later, the prover adapter should be used to:
1. map witness values into a specific proving tool format
2. run the real prover
3. emit a real proof artifact
4. generate verifier calldata
5. feed the existing verifier bundle flow

## Current status
This is a skeleton integration layer.
It is the last structural step before implementing a real prover-specific adapter.
