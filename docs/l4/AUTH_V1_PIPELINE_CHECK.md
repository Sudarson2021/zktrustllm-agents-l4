# AUTH_V1 Pipeline Check

## Purpose
This note defines the current end-to-end checked pipeline for the `auth_v1` ZoKrates path.

## Scripts
Interface validation:
- `scripts/l4/validate_auth_v1_circuit_interface.py`

Pipeline runner:
- `scripts/l4/run_auth_v1_zokrates_pipeline.sh`

## Current pipeline order
1. validate circuit/template/witness interface
2. run compile skeleton
3. run witness skeleton
4. run proof skeleton

## What is checked
The interface validator confirms:
- circuit public parameter order matches template
- circuit private parameter order matches template
- witness public order matches template
- witness private order matches template
- public input count is 7
- private witness count is 5

## Why this matters
This prevents interface drift between:
- the circuit file
- the template
- the witness export
- the execution scripts

## Current status
This is a checked skeleton pipeline.
It is already reproducible even before ZoKrates is installed.

## Future path
When ZoKrates is installed and the circuit matures, the same pipeline should remain the main operational entrypoint.
