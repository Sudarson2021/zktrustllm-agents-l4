# AUTH_V1 Bundle Submission

## Purpose
This note defines the current bundle-driven submission path for `auth_v1`.

## Scripts
Positive path:
- `scripts/l4/submit_auth_v1_verifier_bundle.py`

Negative path:
- `scripts/l4/submit_auth_v1_verifier_bundle_bad_proof.py`

## Submission source of truth
At this stage, the canonical source for on-chain submission is:

- `artifacts/out_l4/verifier_bundle.auth_v1.json`

This means the workflow is now:

1. build deterministic inputs
2. validate inputs
3. build proof payload
4. build circuit input
5. build proof stub
6. validate proof output
7. build prover/verifier bundles
8. submit on-chain from the verifier bundle

## Positive path
The positive bundle path submits:
- agentId
- capabilityId
- contextHash
- traceCommitment
- traceCID
- policyClass
- action
- expiryBucket
- proofBlobHex

to:
- `submitAgentDecisionZK`

## Negative path
The negative bundle path mutates:
- `proofBlobHex`

and confirms that the contract rejects the submission with:
- `authorization proof failed`

## Why this matters
This makes the verifier bundle the stable outer interface for future proof systems.

Later, Groth16 or another proving stack can replace the internal proof artifact, while preserving:
- bundle schema
- submission order
- contract interface
- runtime metadata flow

## Current status
This is still a staged prototype path, but it now has:
- positive acceptance
- negative rejection
- stable bundle interface
