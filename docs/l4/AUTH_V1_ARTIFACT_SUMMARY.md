# AUTH_V1 Artifact Summary

## Purpose
This document summarizes the current L4 `auth_v1` artifact status for reproducibility, review, and paper-facing reporting.

## What is demonstrated
The repository now demonstrates a first real Groth16-backed authorization path for `auth_v1`, including:

1. deterministic input generation
2. circuit-facing input generation
3. ZoKrates-based witness and proof generation
4. generated Groth16 verifier export
5. deployed verifier-backed wrapper validation
6. successful on-chain decision submission
7. negative rejection of a tampered proof

## Main one-command runner
The primary reproducibility entry point is:

- `scripts/l4/run_auth_v1_groth16_repro.sh`

This runner executes both positive and negative paths and writes:
- stage logs under `logs/l4/`
- pipeline events under `artifacts/out_l4/auth_v1_groth16_repro.ndjson`

## Positive-path evidence
The positive path demonstrates:
- direct verifier acceptance
- wrapper acceptance
- successful wrapper submission on-chain
- persisted decision fields:
  - `agentId`
  - `policyClass`
  - `action`
  - `traceCID`
  - `expiryBucket`

Expected positive indicators include:
- `Direct frozen proof verifyTx -> True`
- `Wrapper checkProof() -> True`
- `Preflight submitDecision() -> <decision id>`
- `Submitted Groth16 decision tx -> <tx hash>`

## Negative-path evidence
The negative path mutates a valid proof by flipping one bit and then demonstrates:
- direct verifier rejection
- wrapper rejection
- wrapper submission rejection

Expected negative indicators include:
- `Expected direct verifier rejection captured`
- `Expected wrapper rejection captured`
- `Expected submitDecision() rejection captured`

For malformed Groth16 proofs, the generated verifier may reject by revert rather than returning `False`. This is valid negative-path behavior.

## Key scripts

### Positive path
- `scripts/l4/build_auth_v1_proof_payload.py`
- `scripts/l4/build_auth_v1_circuit_input.py`
- `scripts/l4/run_auth_v1_zokrates_docker.sh`
- `scripts/l4/check_auth_v1_groth16_verifier.py`
- `scripts/l4/check_auth_v1_wrapper_groth16.py`
- `scripts/l4/direct_submit_auth_v1_groth16.py`

### Negative path
- `scripts/l4/build_auth_v1_bad_groth16_proof.py`
- `scripts/l4/check_auth_v1_groth16_verifier_bad.py`
- `scripts/l4/check_auth_v1_wrapper_groth16_bad.py`
- `scripts/l4/direct_submit_auth_v1_groth16_bad.py`

## Key artifacts

### Generated proof artifacts
- `artifacts/out_l4/zokrates_docker/proof.json`
- `artifacts/out_l4/zokrates_docker/proof.frozen.json`
- `artifacts/out_l4/zokrates_docker/proof.bad.json`

### Deterministic input artifacts
- `artifacts/out_l4/proof_payload.auth_v1.json`
- `artifacts/out_l4/circuit_input.auth_v1.json`

### Pipeline output
- `artifacts/out_l4/auth_v1_groth16_repro.ndjson`

## Deployment state
The current flow uses:
- a generated verifier contract exported from the current ZoKrates proving/verification key pair
- `DecisionAttestorGroth16.sol` as the Groth16-capable wrapper
- deployed addresses recorded in `deployments/l4.localhost.json`

## Git milestones
Relevant tags:
- `l4-auth-v1-first-real-groth16-submit`
- `l4-auth-v1-groth16-negative-test`
- `l4-auth-v1-groth16-repro`

## Reviewer-facing conclusion
The `auth_v1` L4 path now supports a reproducible real Groth16 workflow with:
- verifier-accepted valid proofs
- wrapper-accepted valid proofs
- successful on-chain decision submission
- rejection of tampered proofs across verifier, wrapper, and submission stages
