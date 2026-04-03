# First Real ZK Path: Agent Authorization + Context Binding

## Public Inputs
1. agentKey
2. capabilityId
3. policyClassHash
4. contextHash
5. traceCommitment
6. actionHash
7. expiryBucket

## Security Goal
Prove that a submitted decision:
- belongs to a registered and authorized agent,
- is tied to a valid short-lived capability,
- matches the intended policy class,
- is bound to the observed context,
- is bound to the evidence trace,
- selects one bounded mitigation action,
- and is only valid for a bounded time window.

## Bounded Action Set
- keep
- rekey
- rotate
- isolate
- quarantine

## Why this is the first proof target
This is smaller and safer than full policy-compliance proof.
It directly upgrades the current mock decision path toward a real proof-governed L4 path.
