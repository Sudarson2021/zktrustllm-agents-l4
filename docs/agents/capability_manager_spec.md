# CapabilityManager Specification

## Purpose
This document defines the initial specification for the `CapabilityManager` component in the L4 ZKTrustLLM-Agents control plane.

The `CapabilityManager` is responsible for issuing and validating short-lived least-privilege capabilities so that:
- registered agents receive bounded permissions,
- task scope remains explicit,
- actions remain policy-aware,
- expired or out-of-scope capabilities are rejected.

---

## 1. Scope

The initial `CapabilityManager` is responsible for:
- issuing capabilities to registered active agents
- storing bounded scope metadata
- validating expiry
- validating action class and policy class
- revoking capabilities when needed

The initial `CapabilityManager` is not responsible for:
- registering agents
- evaluating trust state
- selecting policy actions
- verifying Groth16 proofs directly

---

## 2. Core Entity

Each capability should have the following fields:

- `capabilityId`
- `agentId`
- `agentAddress`
- `policyClass`
- `actionClass`
- `scopeHash`
- `contextHash`
- `issuedAt`
- `expiry`
- `status`

---

## 3. Field Definitions

### 3.1 capabilityId
A unique identifier for the capability.

### 3.2 agentId
The logical agent identifier to which the capability belongs.

### 3.3 agentAddress
The bound agent address.

### 3.4 policyClass
The policy namespace under which the capability is valid.

Examples:
- `context-collect`
- `trust-evaluate`
- `policy-enforce`

### 3.5 actionClass
The bounded action class permitted by the capability.

Initial action classes:
- `keep`
- `rekey`
- `rotate`
- `isolate`
- `quarantine`

### 3.6 scopeHash
A hash describing the allowed scope of the capability.

### 3.7 contextHash
The bounded context to which the capability is tied.

### 3.8 issuedAt
Timestamp of issuance.

### 3.9 expiry
Timestamp after which the capability is invalid.

### 3.10 status
Lifecycle state of the capability.

Initial states:
- `Valid`
- `Revoked`
- `Expired`

---

## 4. Required Functions

### 4.1 issueCapability
Purpose:
- issue a new capability to an active registered agent

Inputs:
- `agentId`
- `agentAddress`
- `policyClass`
- `actionClass`
- `scopeHash`
- `contextHash`
- `expiry`

Checks:
- agent must exist in `AgentRegistry`
- agent must be active
- expiry must be in the future
- policy class must be valid
- action class must be valid

Output:
- new capability record and issuance event

### 4.2 revokeCapability
Purpose:
- revoke a capability before expiry

Input:
- `capabilityId`

Checks:
- capability must exist
- capability must not already be revoked

Output:
- status changes to `Revoked`

### 4.3 isCapabilityValid
Purpose:
- confirm that a capability is currently usable

Checks:
- capability exists
- status is `Valid`
- current time is before expiry

Output:
- boolean validity result

### 4.4 isCapabilityUsableFor
Purpose:
- confirm that a capability is valid for a requested policy/action/context combination

Inputs:
- `capabilityId`
- `policyClass`
- `actionClass`
- `contextHash`

Checks:
- capability is valid
- requested policy class matches stored policy class
- requested action class matches stored action class
- requested context hash matches stored context hash

Output:
- boolean usability result

### 4.5 getCapability
Purpose:
- return stored capability fields

### 4.6 expireCapabilityView
Purpose:
- interpret whether an otherwise valid capability should be considered expired by time

---

## 5. Events

The initial version should emit:

### 5.1 CapabilityIssued
Fields:
- `capabilityId`
- `agentId`
- `policyClass`
- `actionClass`
- `expiry`

### 5.2 CapabilityRevoked
Fields:
- `capabilityId`

---

## 6. Initial Validation Rules

### Rule CM1
Capabilities may only be issued to agents that are registered and active.

### Rule CM2
A valid capability must be short-lived.

### Rule CM3
A valid capability must be scope-bound.

### Rule CM4
A valid capability must be context-bound.

### Rule CM5
A revoked capability must fail all usability checks.

### Rule CM6
An expired capability must fail all usability checks.

---

## 7. Relationship to Other Components

### With AgentRegistry
The manager must consult the registry before issuing a capability.

### With Gateway
The gateway uses capability checks to validate:
- sender scope
- task scope
- policy class
- freshness
- admissibility for requested action

### With Trust and Policy Logic
Trust or policy outcomes may later trigger revocation, but the manager itself only stores and evaluates capability validity.

### With Proof Logic
Later Groth16 authorization proofs may bind to:
- `capabilityId`
- `scopeHash`
- `contextHash`
- `policyClass`
- `actionClass`

---

## 8. Suggested Solidity Representation

A first Solidity version can use:
- a struct for `CapabilityRecord`
- a mapping from `capabilityIdHash` to record
- enum types for `actionClass` and `status`

---

## 9. Initial Non-goals

The initial capability manager should not:
- compute trust state
- store raw evidence
- decide mitigations
- carry media traffic
- replace gateway validation

---

## 10. Status

This document freezes the initial contract-facing specification for `CapabilityManager` in the L4 ZKTrustLLM-Agents control plane.
