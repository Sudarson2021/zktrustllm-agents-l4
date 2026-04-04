# AUTH_V1 ZoKrates Bridge

## Purpose
This note defines the first concrete proving-tool bridge for `auth_v1` using a ZoKrates-oriented placeholder workflow.

## Scripts
Input exporter:
- `scripts/l4/export_auth_v1_zokrates_inputs.py`

Proof artifact builder:
- `scripts/l4/build_auth_v1_zokrates_proof_artifact.py`

## Artifacts
- `artifacts/out_l4/zokrates_input.auth_v1.json`
- `artifacts/out_l4/zokrates_proof.auth_v1.placeholder.json`

## What the bridge does
The bridge maps the stable repository workflow into a ZoKrates-friendly shape:

1. witness export
2. ordered public inputs
3. ordered private witness values
4. flat argument list for witness computation
5. placeholder ZoKrates proof artifact
6. placeholder verifier calldata slot

## Stable order
Public input order:
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

Private witness order:
1. `scopeHash`
2. `capabilitySalt`
3. `actionCode`
4. `domainSepCapability`
5. `domainSepAction`

## Why this matters
This makes the next migration step much easier:

- the repository already has deterministic witness exports
- the field order is fixed
- the proof artifact shape is defined
- the outer bundle workflow stays unchanged

## Future replacement path
Later, replace:
- placeholder witness CLI example
- placeholder ZoKrates proof artifact
- empty verifier calldata

with:
- actual ZoKrates witness computation
- actual `proof.json`
- actual exported verifier calldata

## Current status
This is still a bridge placeholder, not a real proof path yet.
It is the first concrete proving-tool integration layer for `auth_v1`.
