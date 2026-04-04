# AUTH_V1 Hashing Specification

## Purpose
This note defines the deterministic hashing and encoding rules for the first real authorization-proof target:

**auth_v1 = agent authorization + context binding + trace binding + bounded action binding**

The goal is to keep:
- off-chain witness generation
- test-vector generation
- on-chain verification

aligned to the same canonical inputs.

## Public inputs
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

## Canonical hash rules

### policyClassHash
`policyClassHash = keccak256(bytes(policyClass))`

### actionHash
`actionHash = keccak256(bytes(action))`

### scopeHash
`scopeHash = keccak256(bytes(scopeText))`

### domain separators
- `domainSepCapability = keccak256("ZKTrustLLM-Agents/auth_v1/capability")`
- `domainSepAction = keccak256("ZKTrustLLM-Agents/auth_v1/action")`

## Draft witness-side digests

### capabilityWitnessDigestDraft
`keccak256(abi.encode(domainSepCapability, agentKey, policyClassHash, scopeHash, expiryBucket, capabilitySalt))`

### actionWitnessDigestDraft
`keccak256(abi.encode(domainSepAction, actionCode))`

## Public input digest
`keccak256(abi.encode(agentKey, capabilityId, policyClassHash, contextHash, traceCommitment, actionHash, expiryBucket))`

## Bounded action code mapping
- `1 = keep`
- `2 = rekey`
- `3 = rotate`
- `4 = isolate`
- `5 = quarantine`

## Important note
At the current prototype stage:
- `capabilityId` is still produced by the current capability flow
- `capabilityWitnessDigestDraft` is a future-proof draft relation
- it is **not yet required** to equal the current runtime `capabilityId`

## Output files
The deterministic input builder writes:
- `artifacts/out_l4/auth_v1_inputs.task-0001.json`
- `configs/l4/test_vectors_auth_v1.json`
