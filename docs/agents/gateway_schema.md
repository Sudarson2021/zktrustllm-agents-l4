# ZKTrustLLM-Agents Secure Gateway Schema

## Purpose
This document defines the initial secure inter-agent gateway schema and validation logic.

The secure gateway is treated as a first-class control component.
Its job is to ensure that every inter-agent exchange is:
- structured,
- signed,
- context-scoped,
- capability-limited,
- policy-aware,
- freshness-checked.

---

# 1. Required Gateway Message Fields

Every inter-agent message must contain the following fields:
- `senderAgentId`
- `receiverAgentId`
- `taskId`
- `capabilityId`
- `contextHash`
- `payloadHash`
- `policyClass`
- `timestamp`
- `signature`

---

# 2. Field Semantics

## 2.1 senderAgentId
Unique identifier of the sending agent.

## 2.2 receiverAgentId
Unique identifier of the intended receiving agent or gateway-approved endpoint.

## 2.3 taskId
Unique identifier for the current bounded workflow task.

## 2.4 capabilityId
Identifier of the short-lived least-privilege capability used for this message.

## 2.5 contextHash
Commitment to the active bounded context for the task.

## 2.6 payloadHash
Digest of the message payload or referenced content.

## 2.7 policyClass
Policy namespace or action-governance class under which this message is allowed.

## 2.8 timestamp
Freshness marker used to reject replayed or stale messages.

## 2.9 signature
Digital signature over the approved message structure.

---

# 3. Minimal Message Model

Example message:
- `senderAgentId`: agent-001
- `receiverAgentId`: agent-002
- `taskId`: task-0001
- `capabilityId`: cap-12345
- `contextHash`: 0x...
- `payloadHash`: 0x...
- `policyClass`: context-collect
- `timestamp`: 1770000000
- `signature`: 0x...

---

# 4. Gateway Validation Pipeline

The gateway must validate messages in this order.

## V1. Sender identity validation
Check:
- sender exists in AgentRegistry
- sender is not revoked
- sender role is allowed for this message type

Failure result:
- `REJECT_IDENTITY`

## V2. Receiver authorization validation
Check:
- receiver exists
- sender is allowed to contact receiver for the current task/policy class

Failure result:
- `REJECT_RECEIVER_AUTH`

## V3. Capability validity check
Check:
- capability exists
- capability is not expired
- capability belongs to sender
- capability scope matches task and message type

Failure result:
- `REJECT_CAPABILITY`

## V4. Context-scope validation
Check:
- contextHash is present
- contextHash matches active task context
- sender is not attempting to reuse a different context scope improperly

Failure result:
- `REJECT_SCOPE`

## V5. Payload-integrity validation
Check:
- payloadHash matches actual payload or approved referenced content

Failure result:
- `REJECT_PAYLOAD`

## V6. Policy-class validation
Check:
- message is permitted under the declared policyClass
- sender role is allowed under that policy class

Failure result:
- `REJECT_POLICY`

## V7. Freshness validation
Check:
- timestamp is within allowed replay window
- task is still active
- capability TTL remains valid

Failure result:
- `REJECT_FRESHNESS`

## V8. Signature validation
Check:
- signature verifies against sender key material
- signed structure matches approved field ordering

Failure result:
- `REJECT_SIGNATURE`

If all checks pass:
- `ACCEPT`

---

# 5. Gateway Outcomes

The gateway should emit exactly one status per message:
- `ACCEPT`
- `REJECT_IDENTITY`
- `REJECT_RECEIVER_AUTH`
- `REJECT_CAPABILITY`
- `REJECT_SCOPE`
- `REJECT_PAYLOAD`
- `REJECT_POLICY`
- `REJECT_FRESHNESS`
- `REJECT_SIGNATURE`

---

# 6. Gateway Logging Requirements

Every validation attempt should produce a bounded log record containing:
- messageId or derived message reference
- senderAgentId
- receiverAgentId
- taskId
- capabilityId
- policyClass
- timestamp
- validation outcome
- rejection class if any
- trace reference / traceCID if available

The gateway log should not store raw sensitive evidence unless explicitly allowed by policy.

---

# 7. Initial Security Rules

## Rule G1
Unsigned messages must never be forwarded.

## Rule G2
Capabilities are short-lived and least-privilege by default.

## Rule G3
A valid sender identity does not imply valid scope.

## Rule G4
A valid capability does not imply policy admissibility.

## Rule G5
Messages outside freshness bounds must be rejected even if signature and identity are valid.

## Rule G6
Payload integrity must be checked before policy-dependent forwarding.

---

# 8. Initial Non-goals

At this stage the gateway is not intended to:
- transport bulk media
- replace DTLS, QUIC, RTP, or SRTP
- expose unrestricted raw trust evidence to arbitrary agents
- bypass policy or capability checks for convenience

---

# 9. Relationship to the Current L4 Baseline

The current `auth_v1` Groth16 path remains the cryptographic baseline for commitment-bound authorization logic.

The secure gateway defined here is the next control-plane layer that will later integrate with:
- AgentRegistry
- CapabilityManager
- DecisionAttestor
- PolicyRegistry
- anomaly and trust-state logic

---

# 10. Status

This schema is the initial frozen secure-gateway contract for inter-agent communication in the L4 control plane.
