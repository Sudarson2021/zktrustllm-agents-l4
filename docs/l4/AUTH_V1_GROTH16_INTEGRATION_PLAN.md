# AUTH_V1 Groth16 Integration Plan

## Goal
Replace the current mock proof stub path with a real Groth16-style proof workflow while preserving the existing outer interface.

## Current stable interface chain
1. deterministic inputs
2. input validation
3. proof payload
4. circuit input
5. mock proof output
6. proof-output validation
7. prover bundle
8. verifier bundle
9. positive verifier-bundle submission
10. negative verifier-bundle rejection

## What should remain stable
The following should remain stable during Groth16 integration:
- `configs/l4/test_vectors_auth_v1.json`
- `artifacts/out_l4/proof_payload.auth_v1.json`
- `artifacts/out_l4/circuit_input.auth_v1.json`
- `artifacts/out_l4/witness_input.auth_v1.json`
- `artifacts/out_l4/prover_bundle.auth_v1.json`
- `artifacts/out_l4/verifier_bundle.auth_v1.json`

Also preserve:
- public input order
- private witness order
- runtime metadata fields
- `submitAgentDecisionZK` outer contract interface

## Planned replacement path

### Stage A: circuit implementation
Implement the first real circuit `auth_v1` with public inputs:
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

Private witness:
1. `scopeHash`
2. `capabilitySalt`
3. `actionCode`
4. `domainSepCapability`
5. `domainSepAction`

### Stage B: witness generation
Use:
- `artifacts/out_l4/witness_input.auth_v1.json`

to generate witness inputs in the format expected by the proving toolchain.

### Stage C: proof generation
Replace:
- `scripts/l4/build_auth_v1_proof_stub.py`

with a real prover adapter that emits:
- proof artifact
- public inputs array
- verifier-ready calldata or JSON

### Stage D: verifier replacement
Replace:
- `MockAuthorizationVerifierV2.sol`

with a generated Groth16 verifier or equivalent verifier contract.

Keep:
- `DecisionAttestorZK.sol`

so the surrounding architecture does not need redesign.

### Stage E: bundle continuity
Keep:
- `prover_bundle.auth_v1.json`
- `verifier_bundle.auth_v1.json`

as the stable integration layer.

Only change the internal proof artifact contents.

## Immediate implementation tasks
1. export circuit-friendly witness input
2. fix circuit template and field order
3. write prover adapter skeleton
4. introduce real proof artifact schema
5. deploy real verifier contract
6. re-run positive and negative bundle submission tests

## Expected future artifacts
- `witness_input.auth_v1.json`
- `proof_output.auth_v1.real.json`
- `verifier_calldata.auth_v1.json`
- generated verifier contract artifact

## Why this is the right migration
This plan lets the project move from:
- staged mock proof flow

to:
- real proof-backed authorization

without changing the high-level L4 system design.

This preserves reproducibility, traceability, and journal-quality engineering structure.
