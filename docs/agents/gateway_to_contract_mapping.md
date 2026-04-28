# Gateway to Contract Mapping

## Purpose
This document maps the secure gateway validation model to concrete contract responsibilities in the L4 ZKTrustLLM-Agents control plane.

It explains which contract or subsystem should answer each validation question raised by the gateway.

The goal is to ensure that:
- gateway logic remains structured,
- contract boundaries remain clear,
- proof inputs can later be aligned with contract state,
- implementation does not blur responsibilities.

---

## 1. Main Components in Scope

The initial mapping uses:
- `AgentRegistry.sol`
- `CapabilityManager.sol`
- future `PolicyRegistry.sol`
- future decision / attestation contracts
- off-chain gateway validation logic

---

## 2. Validation Step Mapping Overview

| Gateway Step | Main Source of Truth |
|---|---|
| Sender identity validation | `AgentRegistry.sol` |
| Receiver authorization validation | gateway logic + registry/policy checks |
| Capability validity check | `CapabilityManager.sol` |
| Context-scope validation | gateway logic + capability context binding |
| Payload-integrity validation | off-chain hashing / evidence processor |
| Policy-class validation | future `PolicyRegistry.sol` + capability checks |
| Freshness validation | gateway logic + capability expiry |
| Signature validation | off-chain cryptographic verification |

---

## 3. Detailed Mapping

### 3.1 Sender Identity Validation
Question:
- Is the sender known, active, and role-valid?

Primary component:
- `AgentRegistry.sol`

Expected checks:
- agent exists
- agent status is `Active`
- role is one of the allowed initial control-plane roles

Relevant functions:
- `getAgent(...)`
- `isActiveAgent(...)`
- `isRoleAllowed(...)`

### 3.2 Receiver Authorization Validation
Question:
- Is the sender allowed to contact the intended receiver for the requested workflow?

Primary component:
- gateway logic in the initial implementation

Supporting components:
- `AgentRegistry.sol`
- future `PolicyRegistry.sol`

Expected checks:
- receiver exists
- receiver is active
- sender role / receiver role pairing is allowed
- task and policy path are admissible

### 3.3 Capability Validity Check
Question:
- Does the sender hold a valid non-revoked non-expired capability?

Primary component:
- `CapabilityManager.sol`

Expected checks:
- capability exists
- capability is not revoked
- current time is before expiry
- capability belongs to the expected agent

Relevant functions:
- `isCapabilityValid(...)`
- `getCapability(...)`

### 3.4 Context-Scope Validation
Question:
- Is the request tied to the correct bounded context?

Primary component:
- gateway logic in the first implementation

Supporting component:
- `CapabilityManager.sol`

Expected checks:
- request context hash equals stored capability context hash
- capability scope hash is compatible with the request
- sender is not reusing capability outside intended task context

Relevant function:
- `isCapabilityUsableFor(...)`

### 3.5 Payload-Integrity Validation
Question:
- Does the declared payload hash match the actual payload?

Primary component:
- off-chain hashing / evidence processor

Supporting relation:
- future proof inputs may bind payload or evidence commitments

Current note:
- this is not a direct on-chain responsibility in the first gateway version

### 3.6 Policy-Class Validation
Question:
- Is the request allowed under the declared policy class?

Primary component:
- future `PolicyRegistry.sol`

Supporting component:
- `CapabilityManager.sol`

Expected checks:
- policy class exists
- requesting role is allowed for the policy class
- requested action is allowed for the resulting trust state
- capability policy binding matches request policy

### 3.7 Freshness Validation
Question:
- Is the request still within permitted time bounds?

Primary component:
- gateway logic

Supporting component:
- `CapabilityManager.sol`

Expected checks:
- message timestamp is within replay window
- capability expiry remains valid
- task window is still active

### 3.8 Signature Validation
Question:
- Is the message signature valid for the declared sender?

Primary component:
- off-chain signature verification

Supporting component:
- `AgentRegistry.sol`

Expected checks:
- sender public identity/address exists
- signature matches the approved signed fields
- signature corresponds to the registered sender identity

---

## 4. Initial Contract Responsibility Split

### AgentRegistry.sol
Responsible for:
- agent existence
- role metadata
- status metadata
- active / suspended / revoked state

Not responsible for:
- capability issuance
- policy decisions
- proof verification
- media transport

### CapabilityManager.sol
Responsible for:
- capability issuance
- revocation
- expiry-aware validity
- context-bound usability checks

Not responsible for:
- agent registration
- policy matrix ownership
- proof verification
- trust-state computation

### PolicyRegistry.sol (future)
Responsible for:
- policy class definitions
- allowed role-to-policy mappings
- trust-state to action admissibility
- bounded action discipline

---

## 5. Direction for Future Proof Binding

A later proof path should be able to bind selected gateway-relevant values, including:
- `agentId`
- `capabilityId`
- `policyClass`
- `actionClass`
- `contextHash`

This will let the system prove bounded authorization and policy admissibility without exposing raw sensitive evidence.

---

## 6. Status

This document freezes the initial gateway-to-contract responsibility mapping for the L4 ZKTrustLLM-Agents control plane.
