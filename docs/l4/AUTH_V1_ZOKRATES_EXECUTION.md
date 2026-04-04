# AUTH_V1 ZoKrates Execution

## Purpose
This note defines the operational execution skeleton for the `auth_v1` ZoKrates bridge.

## Scripts
Witness path:
- `scripts/l4/run_auth_v1_zokrates_witness.sh`

Proof path:
- `scripts/l4/run_auth_v1_zokrates_proof.sh`

## Current inputs
The current execution skeleton uses:
- `artifacts/out_l4/zokrates_input.auth_v1.json`

It extracts:
- `flatArguments`

and records the compute-witness command for reproducibility.

## Current outputs
Command/status logs are written under:
- `logs/l4/zokrates_witness_command.txt`
- `logs/l4/zokrates_witness_status.txt`
- `logs/l4/zokrates_proof_command.txt`
- `logs/l4/zokrates_proof_status.txt`

Flat arguments are written to:
- `artifacts/out_l4/zokrates_run/auth_v1.flat_args.txt`

## Current status
This is an execution skeleton.

If ZoKrates is not installed, the scripts:
- do not fail the workflow unnecessarily
- record the exact command that should be run later
- preserve reproducibility

## Future real execution path
Later, when the actual `auth_v1` circuit is ready, these scripts should be extended to:
1. compile the circuit
2. compute the witness
3. generate the proof
4. export proof JSON
5. convert proof JSON into the real proof artifact
6. feed the existing bundle workflow

## Why this matters
This locks the operational proving path before the real circuit is wired in.
That keeps the L4 workflow stable while the internals mature.
