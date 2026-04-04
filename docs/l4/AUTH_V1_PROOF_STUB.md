# AUTH_V1 Proof Stub

## Purpose
This note defines the current mock proof artifact for the `auth_v1` path.

## Files
Builder:
- `scripts/l4/build_auth_v1_proof_stub.py`

Artifact:
- `artifacts/out_l4/proof_output.auth_v1.mock.json`

Submission consumer:
- `scripts/l4/submit_auth_v1_proof_stub.py`

## Current behavior
The proof stub packages:
- canonical public inputs
- canonical witness placeholders
- a mock proof blob consistent with the current V2 verifier

The current V2 verifier checks:
- `keccak256(proofBlob) == keccak256(abi.encode(public inputs))`

So the proof stub is the final pre-Groth16 interface layer.

## Future replacement
Later, this file should be replaced by a real proof artifact containing:
- prover output
- public input array
- verifier-ready calldata or JSON bundle
