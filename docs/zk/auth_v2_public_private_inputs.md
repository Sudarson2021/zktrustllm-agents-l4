# AUTH_V2 Public and Private Inputs

## Purpose
This document defines the first proposed public/private input split for the `auth_v2` proof path.

The goal is to make explicit:
- which fields should be verifier-visible
- which fields should remain witness-side
- why each field belongs in that category

---

## 1. Design Principle

Fields should be public if they must be:
- checked by the verifier
- referenced by the wrapper or contract layer
- externally bound to the submitted decision

Fields should remain private if they:
- reveal unnecessary sensitive detail
- are only needed to satisfy the internal relation
- can be represented through commitments rather than disclosure

---

## 2. Proposed Public Inputs

The first `auth_v2` version should expose the following public inputs.

### 2.1 agentKey or agentIdHash
Reason:
- binds the proof to a specific requesting agent identity representation

### 2.2 capabilityId
Reason:
- binds the proof to a specific issued capability

### 2.3 policyClassHash
Reason:
- binds the proof to the declared policy namespace

### 2.4 actionClass value or hash
Reason:
- binds the proof to the bounded requested action

### 2.5 contextHash
Reason:
- binds the proof to the bounded request context

### 2.6 traceCommitment
Reason:
- allows later trace-linked audit reference without disclosing raw evidence

### 2.7 expiryBucket
Reason:
- expresses bounded temporal validity in verifier-visible form

---

## 3. Proposed Private Inputs

The first `auth_v2` version should keep the following values private or witness-side.

### 3.1 raw capability metadata
Reason:
- the proof only needs to show bounded relation satisfaction, not full metadata disclosure

### 3.2 raw policy metadata
Reason:
- the proof should bind the policy class, not reveal unnecessary full policy details

### 3.3 raw agent metadata
Reason:
- off-chain metadata should remain outside public verifier inputs

### 3.4 witness-side relation helpers
Reason:
- internal equality helpers, normalisation values, and compatibility helpers do not need to be public

### 3.5 any raw evidence material
Reason:
- raw evidence should remain off-path and private unless specifically committed and disclosed by policy

---

## 4. Initial Public Input Ordering

The first proposed public ordering is:

1. `agentKey`
2. `capabilityId`
3. `policyClassHash`
4. `actionClass`
5. `contextHash`
6. `traceCommitment`
7. `expiryBucket`

This preserves the same public input count as the earlier `auth_v1` path, which is useful for incremental migration and debugging.

---

## 5. Wrapper Alignment

The wrapper and submission scripts should later read these same public fields when constructing:
- contract submissions
- gateway validation traces
- audit-facing summaries

This alignment is important because it keeps:
- proof semantics
- contract semantics
- gateway semantics

in the same field order and meaning.

---

## 6. Initial Mapping to Existing L4 Components

### AgentRegistry
Relevant bound field:
- `agentKey` or `agentIdHash`

### CapabilityManager
Relevant bound field:
- `capabilityId`

### PolicyRegistry
Relevant bound fields:
- `policyClassHash`
- `actionClass`

### Gateway Request
Relevant bound fields:
- `contextHash`
- `traceCommitment`
- `expiryBucket`

---

## 7. First AUTH_V2 Non-goals

The first AUTH_V2 input split should not yet attempt to encode:
- full trust-state transition logic
- gateway signature verification
- payload-hash equality logic
- full policy matrix proof branching
- on-chain state inclusion proofs

Those can be added later after the first control-plane-aware relation works end to end.

---

## 8. Status

This document freezes the first proposed public/private input split for the AUTH_V2 proof path.
