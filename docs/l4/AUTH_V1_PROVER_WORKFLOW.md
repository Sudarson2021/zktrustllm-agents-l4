# AUTH_V1 Prover Workflow

## Goal
Define the practical workflow for moving from deterministic `auth_v1` inputs to a real proof-backed authorization path.

## Inputs
The workflow starts from:
- `configs/l4/test_vectors_auth_v1.json`

This file is validated by:
- `scripts/l4/validate_auth_v1_inputs.py`

Then converted into a canonical prover payload by:
- `scripts/l4/build_auth_v1_proof_payload.py`

## Current artifacts
- `artifacts/out_l4/auth_v1_inputs.task-0001.json`
- `configs/l4/test_vectors_auth_v1.json`
- `artifacts/out_l4/proof_payload.auth_v1.json`

## Planned real proving stages

### Stage 1: deterministic inputs
Status: complete

Outputs:
- normalized public inputs
- stable witness placeholders
- stable digest values
- test vectors

### Stage 2: prover payload
Status: complete

Outputs:
- canonical payload for a future prover
- fixed field names and action mapping
- stable separation between public inputs and witness placeholders

### Stage 3: real circuit implementation
Status: next

Target relation:
- prove authorization and bounded action binding for `auth_v1`

Expected public inputs:
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

Expected witness placeholders:
1. `scopeHash`
2. `capabilitySalt`
3. `actionCode`
4. `domainSepCapability`
5. `domainSepAction`

### Stage 4: proof generation
Status: future

Expected outputs:
- proof blob
- public inputs array
- verifier-compatible calldata or JSON bundle

### Stage 5: on-chain verification
Status: future

Expected path:
- replace `MockAuthorizationVerifierV2.sol`
- keep `DecisionAttestorZK.sol`
- submit real proof-backed authorization decisions

## Recommended implementation order
1. preserve current `auth_v1` payload format
2. implement the first circuit using the same public inputs
3. generate deterministic test proofs locally
4. connect generated verifier to `DecisionAttestorZK`
5. extend the L4 demo runner with a real ZK path

## Immediate engineering rule
Do not change field names in:
- `test_vectors_auth_v1.json`
- `proof_payload.auth_v1.json`

These should remain the stable interface between:
- the current prototype,
- the first circuit implementation,
- and the future journal artifact.
