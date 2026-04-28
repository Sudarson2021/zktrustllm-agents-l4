# AUTH_V2 Relation v0

## Purpose
This document defines the first concrete relation for the AUTH_V2 proof path.

The goal of relation v0 is to keep the first control-plane-aware proof simple enough to:
- implement quickly,
- debug easily,
- preserve the seven-public-input structure,
- bind the proof to L4 control-plane semantics.

---

## 1. Main Idea

Relation v0 binds a request to:
- `agentKey`
- `capabilityId`
- `policyClassHash`
- `actionClass`
- `contextHash`
- `expiryBucket`

and derives a public `traceCommitment` from those values plus one private witness value:
- `bindingNonce`

This gives a first useful cryptographic relation without requiring:
- signature verification in-circuit
- payload hashing in-circuit
- full policy branching in-circuit

---

## 2. Relation Definition

The first AUTH_V2 relation is:

`traceCommitment = (agentKey + capabilityId + policyClassHash + actionClass + contextHash + expiryBucket + bindingNonce) mod BN128_SCALAR_FIELD`

Where:
- `agentKey` is public
- `capabilityId` is public
- `policyClassHash` is public
- `actionClass` is public
- `contextHash` is public
- `traceCommitment` is public
- `expiryBucket` is public
- `bindingNonce` is private

---

## 3. Why This Is the Right First Step

This relation is intentionally simple.

It is strong enough to show that:
- the proof is no longer generic authorization only,
- the proof is now tied to real L4 control-plane fields,
- a verifier can check a bounded relation over those fields,
- the witness still contains a hidden value (`bindingNonce`).

It is also small enough to avoid unnecessary circuit complexity in the first AUTH_V2 implementation.

---

## 4. Initial Non-goals

Relation v0 does not yet prove:
- agent registration on-chain
- capability existence on-chain
- policy rule lookup on-chain
- trust-state transition correctness
- signature correctness
- payload integrity

Those remain outside the first circuit and are still handled by the control-plane contracts and gateway logic.

---

## 5. Expected Use

Relation v0 should be used to:
1. generate the first AUTH_V2 payload,
2. generate the first AUTH_V2 circuit input,
3. build the first `auth_v2.zok` circuit,
4. test valid proof acceptance,
5. test tampered proof rejection.

---

## 6. Status

This document freezes the first concrete AUTH_V2 control-plane-aware relation, called relation v0.
