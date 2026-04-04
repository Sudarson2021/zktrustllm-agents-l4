# First Real Authorization Circuit Relation (`auth_v1`)

## Goal
Move from the current mock / V2 structured-input verifier toward the first real proof-backed authorization circuit for:

**ZKTrustLLM-Agents: Proof-Governed Zero-Trust Multi-LLM Orchestration**

This first circuit should prove:
- the decision is bound to an authorized agent,
- the decision is bound to a short-lived capability,
- the decision is tied to the correct policy class,
- the decision is bound to the observed context,
- the decision is bound to the evidence trace,
- the selected action is one of a bounded allowed set,
- the proof is valid only for a bounded expiry window.

## Public Inputs
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

## Private Witness (first practical version)
1. `scopeHash`
2. `capabilitySalt`
3. `actionCode`
4. `domainSepCapability`
5. `domainSepAction`

## Bounded action set
Suggested fixed integer mapping:
- `1 = keep`
- `2 = rekey`
- `3 = rotate`
- `4 = isolate`
- `5 = quarantine`

`actionHash` is derived from the chosen bounded `actionCode`.

## First circuit relation
The circuit proves knowledge of witness values such that:

### Constraint 1: capability binding
`capabilityId = H(domainSepCapability, agentKey, policyClassHash, scopeHash, expiryBucket, capabilitySalt)`

This binds the authorization token to:
- a specific agent,
- a specific policy class,
- a specific scope,
- a bounded expiry bucket.

### Constraint 2: bounded action binding
`actionHash = H(domainSepAction, actionCode)`

This binds the proof to one bounded mitigation action.

### Constraint 3: action validity
`actionCode` must be one of the allowed bounded action values:
- `1, 2, 3, 4, 5`

### Constraint 4: context binding
The proof is generated over the supplied `contextHash`.

### Constraint 5: trace binding
The proof is generated over the supplied `traceCommitment`.

## On-chain interpretation
The contract still performs:
- registered-agent check,
- capability validity check,
- capability ownership check.

The circuit adds:
- cryptographic binding between capability, policy class, context, trace, and bounded action.

## Why `auth_v1` is the right first real proof
This is deliberately smaller than a full policy-compliance proof.

It upgrades the current pipeline from:
- mock proof acceptance,
- then structured-input consistency checking,

toward:
- a real authorization proof with bounded action semantics.

## What remains out of scope for `auth_v1`
Not yet included:
- Merkle inclusion against an on-chain root of authorized capabilities
- proof of full policy semantics
- proof of dynamic trust-score computation
- proof of anomaly reasoning correctness
- Groth16 performance tuning / recursion / aggregation

## Next verifier upgrade after `auth_v1`
After the first circuit is stable, the next proof step should add:

### `auth_v2`
- capability inclusion proof against a commitment root or authorization root
- optional nullifier to prevent replay
- stronger expiry-window semantics
- optional anomaly-root binding

## Suggested implementation order
1. keep the current `DecisionAttestorZK.sol`
2. replace `MockAuthorizationVerifierV2.sol` with a generated verifier
3. keep the same public inputs
4. generate proof + verify on-chain
5. extend the L4 demo runner to exercise the real proof path

