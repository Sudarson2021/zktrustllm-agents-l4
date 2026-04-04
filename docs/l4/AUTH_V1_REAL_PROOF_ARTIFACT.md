# AUTH_V1 Real Proof Artifact

## Purpose
This note defines the future-proof artifact schema for the first real `auth_v1` proof path.

## Current builder
- `scripts/l4/build_auth_v1_real_proof_placeholder.py`

## Current validator
- `scripts/l4/validate_auth_v1_real_proof_placeholder.py`

## Current artifact
- `artifacts/out_l4/proof_output.auth_v1.real.placeholder.json`

## Why this exists
This placeholder schema lets the project define the stable structure of a future real proof artifact before connecting an actual Groth16 toolchain.

That means the workflow can remain stable while the internal proof generation changes.

## Required fields
The real proof artifact should contain:

- `proofSystem`
- `circuitName`
- `publicInputOrder`
- `publicInputs`
- `proof`
- `derived`
- `runtime`
- `meta`

## Planned real replacement
Later, replace the placeholder fields with actual prover output, such as:
- proof points (`a`, `b`, `c`)
- verifier calldata
- or another verifier-compatible artifact

## Stability rule
Keep stable:
- `publicInputOrder`
- `publicInputs`
- runtime metadata
- task and trace binding
- outer bundle-driven submission workflow

Only replace:
- the internals of the proof artifact
- the verifier implementation
- the calldata-generation layer

## Migration path
1. keep current placeholder schema
2. introduce real witness-to-proof adapter
3. populate actual Groth16 proof fields
4. validate new proof artifact
5. connect generated verifier
6. preserve existing bundle workflow
