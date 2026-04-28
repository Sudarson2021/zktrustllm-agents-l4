# Policy Action Matrix

## Purpose
This document freezes the initial policy-to-action mapping for the L4 ZKTrustLLM-Agents control plane.

It defines:
- which policy classes exist in the first implementation,
- which roles are allowed to operate under each policy class,
- which trust states may lead to which bounded actions,
- which actions are disallowed.

The goal is to make policy execution:
- explicit,
- bounded,
- auditable,
- easy to map into contracts and later proof inputs.

---

## 1. Initial Policy Classes

The initial control-plane policy classes are:
- `context-collect`
- `trust-evaluate`
- `policy-enforce`

---

## 2. Initial Action Classes

The initial bounded action classes are:
- `keep`
- `rekey`
- `rotate`
- `isolate`
- `quarantine`

---

## 3. Initial Trust States

The initial trust states are:
- `Trusted`
- `Degraded`
- `Suspect`
- `Restricted`
- `Quarantined`

---

## 4. Role-to-Policy Mapping

### 4.1 EdgeTelemetryAgent
Allowed policy classes:
- `context-collect`

Disallowed policy classes:
- `trust-evaluate`
- `policy-enforce`

### 4.2 TrustRiskAgent
Allowed policy classes:
- `trust-evaluate`

Disallowed policy classes:
- `context-collect`
- `policy-enforce`

### 4.3 PolicyLKHAgent
Allowed policy classes:
- `policy-enforce`

Disallowed policy classes:
- `context-collect`
- `trust-evaluate`

---

## 5. Policy-to-Action Expectations

### 5.1 context-collect
Typical purpose:
- gather bounded context
- emit context summaries
- emit evidence hashes and trace-linked metadata

Allowed action outcome:
- no direct mitigation action should be executed here

### 5.2 trust-evaluate
Typical purpose:
- interpret verified evidence
- derive trust/risk outcome
- determine admissibility

Allowed action outcome:
- recommendation only
- no direct network/media mitigation execution

### 5.3 policy-enforce
Typical purpose:
- convert admissible trust/risk outputs into bounded mitigation classes

Allowed action outcome:
- `keep`
- `rekey`
- `rotate`
- `isolate`
- `quarantine`

---

## 6. Trust-State to Action Matrix

| Trust State | keep | rekey | rotate | isolate | quarantine |
|---|---|---|---|---|---|
| Trusted | allowed | optional | allowed | disallowed | disallowed |
| Degraded | allowed with caution | allowed | allowed | disallowed by default | disallowed |
| Suspect | disallowed for normal progression | optional | optional | allowed | disallowed by default |
| Restricted | disallowed | optional | optional | allowed | allowed |
| Quarantined | disallowed | disallowed | disallowed | disallowed | required terminal action |

---

## 7. Policy Decision Rules

### Rule PM1
Only `PolicyLKHAgent` may emit final executable action classes.

### Rule PM2
`EdgeTelemetryAgent` may provide context, but must not directly emit mitigation actions.

### Rule PM3
`TrustRiskAgent` may emit trust/risk recommendations, but must not directly execute `keep`, `rekey`, `rotate`, `isolate`, or `quarantine`.

### Rule PM4
`keep` is valid only when the trust state remains operationally admissible.

### Rule PM5
`quarantine` is reserved for `Restricted` or `Quarantined` paths, or equivalent policy override conditions.

### Rule PM6
No action may be executed unless the associated capability, policy class, and context binding are all valid.

---

## 8. Audit Fields for Policy Decisions

Every policy decision should record:
- `agentId`
- `capabilityId`
- `policyClass`
- `actionClass`
- `trustState`
- `contextHash`
- `traceCID`
- `timestamp`
- `decision justification reference`

---

## 9. Contract Mapping Direction

This matrix should later map into:
- `PolicyRegistry.sol`
- `CapabilityManager.sol`
- secure gateway validation
- future `auth_v1` proof inputs for bounded policy admissibility

---

## 10. Status

This document freezes the initial L4 policy-to-action matrix for bounded agentic trust orchestration.
