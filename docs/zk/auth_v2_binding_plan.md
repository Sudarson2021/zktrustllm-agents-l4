# AUTH_V2 Binding Plan

## Purpose
This document defines the first control-plane-aware extension of the current authorization proof path.

The goal of `auth_v2` is to move beyond the earlier authorization-only relation and bind the proof to explicit L4 control-plane semantics.

The first `auth_v2` design should bind:
- agent identity
- capability identity
- policy class
- action class
- context hash

while still preserving the main privacy objective:
- prove bounded authorization and policy admissibility
- without exposing unnecessary raw evidence

---

## 1. Why AUTH_V2 Is Needed

The current `auth_v1` baseline proves a useful authorization relation, but it does not yet fully capture the richer control-plane semantics introduced in the L4 design.

The new L4 control plane now includes:
- registered agents
- issued capabilities
- policy classes
- bounded action classes
- trust-state-aware action admissibility
- gateway-mediated request validation

Because of that, the next proof path must bind the proof to the same objects that the control plane already reasons about.

---

## 2. AUTH_V2 Objective

The first `auth_v2` proof should show that a request is tied to:
- a specific agent
- a specific capability
- a specific policy class
- a specific action class
- a specific bounded context

The proof does not need to prove every possible control-plane condition at once.

The first version should stay narrow and prove only the minimum useful relation needed to connect:
- gateway validation
- contract state meaning
- proof-side authorization semantics

---

## 3. Initial Binding Targets

The first `auth_v2` relation should bind the following fields.

### 3.1 agentKey or agentIdHash
Represents the requesting agent identity in proof-compatible form.

### 3.2 capabilityId
Represents the issued bounded capability used for the request.

### 3.3 policyClassHash
Represents the declared policy namespace under which the request is made.

### 3.4 actionClass
Represents the bounded requested action.

### 3.5 contextHash
Represents the bounded context to which the request is tied.

### 3.6 traceCommitment
Represents the proof-linked trace or evidence commitment.

### 3.7 expiryBucket
Represents bounded time validity for the request.

---

## 4. First AUTH_V2 Claim

The first `auth_v2` proof should aim to prove a statement of the following form:

> A registered agent request is bound to a specific capability, policy class, action class, context hash, and trace commitment, and remains valid within the declared expiry bucket.

This is intentionally narrower than full policy execution.

It does not yet prove:
- the entire trust-state machine
- full gateway signature semantics
- full payload-integrity semantics
- full action execution correctness

It proves the cryptographic binding of the request to the bounded control-plane objects.

---

## 5. Design Principle

AUTH_V2 should follow this principle:

- keep the circuit relation small enough to validate and debug
- reuse the current `auth_v1` working path where possible
- add only the minimum extra public/private inputs needed for control-plane binding
- avoid introducing many new witness rules at once

---

## 6. Relationship to Contracts

AUTH_V2 should align with the existing meaning of:
- `AgentRegistry.sol`
- `CapabilityManager.sol`
- `PolicyRegistry.sol`

The proof does not directly read on-chain state.
Instead, it should bind values whose semantics are already defined by those contracts.

This keeps the proof:
- off-chain computable
- contract-compatible
- easier to explain in the paper

---

## 7. First Implementation Scope

The first AUTH_V2 implementation should include:
1. updated proof payload builder
2. updated circuit input builder
3. new `auth_v2` ZoKrates circuit
4. verifier export
5. wrapper/check script path similar to the current `auth_v1` flow

The first version should not yet include:
- trust-state proof branching
- multiple role-policy branches
- signature verification inside the proof
- payload-hash equality inside the proof
- full gateway rule coverage

---

## 8. Expected Outcome

At the end of the first AUTH_V2 phase, the repository should support:
- construction of a control-plane-aware proof payload
- generation of a real proof for the new relation
- verifier acceptance of a valid proof
- rejection of a tampered proof
- documentation showing how the proof now binds L4 control-plane fields

---

## 9. Status

This document freezes the first AUTH_V2 binding direction for the L4 ZKTrustLLM-Agents proof path.
