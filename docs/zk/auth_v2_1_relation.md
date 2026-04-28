# AUTH_V2.1 Relation

## Purpose
This document defines the next control-plane-aware proof step after AUTH_V2 relation v0.

The goal of AUTH_V2.1 is to extend the current request-binding proof with one bounded policy decision field:
- `policyAdmissibilityFlag`

This keeps the circuit small while making the proof stronger and more meaningful for policy-aware orchestration.

---

## 1. Main Idea

AUTH_V2.1 binds a request to:
- `agentKey`
- `capabilityId`
- `policyClassHash`
- `actionClass`
- `contextHash`
- `expiryBucket`
- `policyAdmissibilityFlag`

and derives a public `traceCommitment` using one private witness value:
- `bindingNonce`

---

## 2. Relation Definition

The AUTH_V2.1 relation is:

`traceCommitment = (agentKey + capabilityId + policyClassHash + actionClass + contextHash + expiryBucket + policyAdmissibilityFlag + bindingNonce) mod BN128_SCALAR_FIELD`

with the additional constraint:

`policyAdmissibilityFlag == 1`

This means the proof only validates when the bounded policy outcome is admissible.

---

## 3. Why This Is the Right Next Step

This extension is useful because it:
- keeps the proof simple,
- preserves explainability,
- connects better to control-plane policy meaning,
- provides a clear bridge toward future trust-state-aware proofs.

---

## 4. Initial Non-goals

AUTH_V2.1 does not yet prove:
- full trust-state transitions
- trust-state history
- signature validation
- full gateway rule coverage
- on-chain policy lookup

---

## 5. Status

This document freezes the first AUTH_V2.1 relation with bounded policy admissibility.
