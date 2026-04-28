# AgentRegistry Specification

## Purpose
This document defines the initial specification for the `AgentRegistry` component in the L4 ZKTrustLLM-Agents control plane.

The `AgentRegistry` is responsible for maintaining the identity and role metadata of registered agents so that:
- only known agents can participate in the control plane,
- role-aware validation can be enforced,
- revoked or inactive agents can be blocked,
- downstream capability issuance remains bound to registered identities.

---

## 1. Scope

The initial `AgentRegistry` is responsible for:
- registering agents
- storing role metadata
- storing agent status
- exposing whether an agent is active, suspended, or revoked
- exposing whether a role is permitted for control-plane participation

The initial `AgentRegistry` is not responsible for:
- issuing capabilities
- evaluating trust state
- selecting policy actions
- storing large evidence objects

---

## 2. Core Entity

Each registered agent should have the following fields:

- `agentId`
- `agentAddress`
- `role`
- `status`
- `registeredAt`
- `updatedAt`
- `metadataHash`

---

## 3. Field Definitions

### 3.1 agentId
A stable identifier for the logical agent, for example:
- `edge-telemetry-01`
- `trust-risk-01`
- `policy-lkh-01`

### 3.2 agentAddress
The blockchain or signing address bound to the agent.

### 3.3 role
The declared control-plane role of the agent.

Initial roles:
- `EdgeTelemetryAgent`
- `TrustRiskAgent`
- `PolicyLKHAgent`

### 3.4 status
The lifecycle state of the agent.

Initial states:
- `Active`
- `Suspended`
- `Revoked`

### 3.5 registeredAt
Timestamp of first registration.

### 3.6 updatedAt
Timestamp of latest status or metadata update.

### 3.7 metadataHash
A hash reference to off-chain agent metadata, description, or config if needed.

---

## 4. Required Functions

The first contract version should support the following functions.

### 4.1 registerAgent
Purpose:
- register a new agent

Inputs:
- `agentId`
- `agentAddress`
- `role`
- `metadataHash`

Checks:
- `agentId` must be unique
- `agentAddress` must not already be assigned to another active record
- `role` must be valid

Output:
- successful registration event

### 4.2 suspendAgent
Purpose:
- temporarily disable an agent without fully revoking it

Input:
- `agentId`

Checks:
- agent must exist
- agent must not already be revoked

Output:
- status changes to `Suspended`

### 4.3 revokeAgent
Purpose:
- permanently disable an agent for control-plane use

Input:
- `agentId`

Checks:
- agent must exist

Output:
- status changes to `Revoked`

### 4.4 reactivateAgent
Purpose:
- restore a suspended agent to active use

Input:
- `agentId`

Checks:
- agent must exist
- agent must currently be `Suspended`

Output:
- status changes to `Active`

### 4.5 updateMetadataHash
Purpose:
- update the off-chain metadata reference for an agent

Inputs:
- `agentId`
- `metadataHash`

Checks:
- agent must exist

Output:
- metadata reference updated

### 4.6 getAgent
Purpose:
- return stored agent fields by `agentId`

### 4.7 isActiveAgent
Purpose:
- return `true` only when the agent exists and status is `Active`

### 4.8 isRoleAllowed
Purpose:
- validate that a role belongs to the approved initial control-plane set

---

## 5. Events

The initial version should emit the following events:

### 5.1 AgentRegistered
Fields:
- `agentId`
- `agentAddress`
- `role`
- `metadataHash`

### 5.2 AgentSuspended
Fields:
- `agentId`

### 5.3 AgentRevoked
Fields:
- `agentId`

### 5.4 AgentReactivated
Fields:
- `agentId`

### 5.5 AgentMetadataUpdated
Fields:
- `agentId`
- `metadataHash`

---

## 6. Initial Validation Rules

### Rule AR1
No agent may be used by the control plane unless it is registered.

### Rule AR2
No revoked agent may pass gateway identity validation.

### Rule AR3
Suspended agents must fail active-agent checks.

### Rule AR4
Only allowed initial roles may be registered.

### Rule AR5
The registry should remain small, explicit, and role-bounded in the initial implementation.

---

## 7. Relationship to Other Components

### With Gateway
The gateway uses the registry to confirm:
- sender exists
- receiver exists
- sender role is valid
- sender status is active

### With CapabilityManager
Capabilities must only be issued to agents that are both:
- registered
- active

### With Trust Logic
Trust state may influence whether an agent becomes suspended or revoked, but the registry itself does not compute trust state.

---

## 8. Suggested Solidity Representation

A first Solidity version can use:
- a struct for `AgentRecord`
- a mapping from `agentIdHash` to record
- a mapping from `agentAddress` to `agentIdHash`
- enum types for `role` and `status`

---

## 9. Initial Non-goals

The initial registry should not:
- embed proof verification logic
- store raw evidence
- perform policy-action selection
- manage transport/media sessions

---

## 10. Status

This document freezes the initial contract-facing specification for `AgentRegistry` in the L4 ZKTrustLLM-Agents control plane.
