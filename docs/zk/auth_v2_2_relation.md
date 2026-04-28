# AUTH_V2.2 Relation

## Purpose
This document defines the next proof step after AUTH_V2.1.

The goal of AUTH_V2.2 is to make the proof trust-state-aware by adding:
- `trustState`

while keeping:
- `policyAdmissibilityFlag`

The first AUTH_V2.2 version proves one bounded admissible pair:
- `trustState == Restricted`
- `actionClass == Isolate`
- `policyAdmissibilityFlag == 1`

---

## 1. Main Idea

AUTH_V2.2 binds a request to:
- `agentKey`
- `capabilityId`
- `policyClassHash`
- `actionClass`
- `contextHash`
- `expiryBucket`
- `policyAdmissibilityFlag`
- `trustState`

and derives a public `traceCommitment` using one private witness:
- `bindingNonce`

---

## 2. Relation Definition

The AUTH_V2.2 relation is:

`traceCommitment = (agentKey + capabilityId + policyClassHash + actionClass + contextHash + expiryBucket + policyAdmissibilityFlag + trustState + bindingNonce) mod BN128_SCALAR_FIELD`

with these bounded constraints:

- `policyAdmissibilityFlag == 1`
- `trustState == 3`
- `actionClass == 3`

This means the first AUTH_V2.2 circuit validates only the admissible pair:
- `Restricted -> Isolate`

---

## 3. Why This Is the Right Next Step

This extension is useful because it:
- introduces trust-state awareness,
- links policy admissibility to a concrete action class,
- stays simple enough to debug,
- creates a clean bridge toward richer policy matrices later.

---

## 4. Initial Non-goals

AUTH_V2.2 does not yet prove:
- multiple trust-state branches in one circuit,
- full on-chain policy lookup,
- signature validation,
- full gateway rule coverage,
- complete trust-state transition history.

---

## 5. Status

This document freezes the first AUTH_V2.2 relation for a trust-state-aware admissible action pair.
