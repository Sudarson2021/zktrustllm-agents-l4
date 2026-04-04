# AUTH_V1 Relation V0

## Purpose
This note defines the first relation-aware version of the `auth_v1` circuit.

## Circuit file
- `circuits/auth_v1.zok`

## Relation notes builder
- `scripts/l4/build_auth_v1_relation_notes.py`

## Relation notes artifact
- `artifacts/out_l4/relation_notes.auth_v1.v0.json`

## What changed from the earlier placeholder
The earlier circuit only checked:
- non-zero bindings
- bounded action code

The new v0 relation keeps the same interface but adds stronger placeholder semantics:
- distinct identity-related bindings
- distinct policy/action-related bindings
- distinct context/trace bindings
- distinct domain separators
- scope separation from the domain separators
- expiry bucket dominance over bounded action code

## Current public input order
1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `contextHash`
5. `traceCommitment`
6. `actionHash`
7. `expiryBucket`

## Current private witness order
1. `scopeHash`
2. `capabilitySalt`
3. `actionCode`
4. `domainSepCapability`
5. `domainSepAction`

## Current v0 constraint set
- all public binding fields are non-zero
- key witness binding fields are non-zero except `capabilitySalt`
- `actionCode` is bounded to `1..5`
- `agentKey != capabilityId`
- `agentKey != policyClassHash`
- `policyClassHash != actionHash`
- `contextHash != traceCommitment`
- `domainSepCapability != domainSepAction`
- `scopeHash != domainSepCapability`
- `scopeHash != domainSepAction`
- `expiryBucket > actionCode`

## Why this matters
This is still not the final proof relation, but it is more scientifically meaningful than a pure placeholder.
It begins to encode:
- identity separation
- evidence/context separation
- domain separation
- bounded action semantics
- time-window linkage

## Next relation target
The next real proof step should replace these placeholder arithmetic constraints with:
- proof-native authorization binding
- proof-native action binding
- proof-native capability binding
- real verifier-compatible constraints
