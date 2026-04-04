# AUTH_V1 Circuit Skeleton

## Purpose
This note defines the first concrete `auth_v1` circuit source file for the ZoKrates path.

## Circuit file
- `circuits/auth_v1.zok`

## Compile script
- `scripts/l4/compile_auth_v1_zokrates.sh`

## Current role
This is a compilable placeholder circuit.
Its purpose is to lock:
- public input order
- private witness order
- parameter names
- compile path
- bounded action-code constraint

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

## Current checks
The placeholder circuit currently checks:
- all current public fields are non-zero
- `expiryBucket > 0`
- `actionCode` is in the bounded placeholder range `1..5`
- key private witness fields are non-zero
- `capabilitySalt` is intentionally left unconstrained because the current placeholder flow may use zero

## Next circuit step
Later, replace the placeholder checks with the actual `auth_v1` proof relation:
- authorization binding
- context binding
- trace binding
- bounded action binding
- expiry binding

## Why this matters
This moves the project from execution skeletons into an actual circuit source path, while preserving the stable outer workflow.
