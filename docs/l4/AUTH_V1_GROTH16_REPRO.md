# AUTH_V1 Groth16 Repro

## Purpose
This note defines the one-command reproducibility path for the real `auth_v1` Groth16 workflow.

## Runner
- `scripts/l4/run_auth_v1_groth16_repro.sh`

## What it covers
The runner executes both positive and negative paths:

### Positive path
1. build payload
2. build circuit input
3. generate proof with ZoKrates Docker path
4. freeze proof
5. verify direct verifier acceptance
6. verify wrapper acceptance
7. submit decision on-chain

### Negative path
1. build tampered proof
2. verify direct verifier rejection
3. verify wrapper rejection
4. verify wrapper submission rejection

## Key artifacts
- `artifacts/out_l4/zokrates_docker/proof.frozen.json`
- `artifacts/out_l4/zokrates_docker/proof.bad.json`
- `artifacts/out_l4/auth_v1_groth16_repro.ndjson`

## Logs
All stage outputs are written under:
- `logs/l4/`

## Success condition
A valid proof is accepted by the verifier and wrapper and is submitted on-chain.
A tampered proof is rejected across verifier and wrapper paths.
