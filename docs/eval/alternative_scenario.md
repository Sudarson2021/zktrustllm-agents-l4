# Alternative Evaluation Scenario

## Scenario Title
Secure IoT multimedia surveillance with privacy-preserving trust orchestration

## Purpose
This scenario serves as an alternative deployment environment for ZKTrustLLM-Agents.

It is used to show that the architecture is not limited to multimedia streaming over 5G-Advanced networks, but can also support privacy-sensitive surveillance and edge-based monitoring systems.

---

## 1. Environment

The target environment consists of:
- distributed surveillance or sensing devices,
- edge nodes collecting and processing multimedia observations,
- trust and policy services controlling access and response,
- a secure control plane coordinating agent decisions,
- off-path audit and evidence storage for later review.

The system must support privacy-preserving trust verification without disclosing raw surveillance evidence unnecessarily.

---

## 2. Actors

The main actors are:
- surveillance devices / sensors
- edge processing nodes
- monitoring operators
- control-plane agents
- trust and policy services
- audit and anchoring components

---

## 3. Assets

The main protected assets are:
- confidentiality of surveillance-related evidence
- correctness of trust decisions
- authorized access to control actions
- integrity of anomaly and mitigation records
- audit trail for later investigation

---

## 4. Threats

Representative threats include:
- compromised sensor or edge device
- unauthorized monitoring request
- replayed or stale control message
- invalid capability use
- tampered trust evidence
- over-disclosure of sensitive surveillance content
- policy-violating escalation request

---

## 5. Trust Decisions

This scenario evaluates whether the system can correctly decide:
- whether a device or node remains trusted,
- whether evidence is strong enough for action,
- whether access to surveillance-related context should be restricted,
- whether a suspect component should be isolated or quarantined,
- whether a recovery path is justified after restriction.

---

## 6. Policy Actions

The bounded action set remains:
- keep
- rekey
- rotate
- isolate
- quarantine

In this scenario the emphasis is on:
- limiting access,
- isolating suspicious components,
- protecting sensitive evidence exposure.

---

## 7. Why This Scenario Is Important

This scenario is valuable because it highlights:
- privacy-sensitive evidence handling,
- strong trust boundaries,
- the need for auditable control decisions,
- the usefulness of zero-knowledge verification beyond multimedia streaming alone.

It also provides a strong contrast with the primary 5G-Advanced multimedia scenario.

---

## 8. Evaluation Questions

The alternative scenario should answer:
1. Can the system verify trust conditions without exposing raw surveillance evidence?
2. Can suspicious devices or nodes be restricted quickly and correctly?
3. Can invalid requests be rejected before policy action is applied?
4. Can the system preserve auditability while minimising disclosure?
5. Can recovery decisions be justified and anchored after restriction or quarantine?

---

## 9. Metrics

Core evaluation metrics for this scenario are:
- unauthorized access rejection rate
- anomaly-to-containment time
- false-accept rate for invalid requests
- trust-state transition correctness
- recovery correctness
- audit completeness

---

## 10. Role in the Paper

This scenario should be used as:
- an alternative deployment case,
- a generalisation example,
- evidence that the architecture extends beyond one single network use case.

---

## 11. Expected Outcome

The expected result is that ZKTrustLLM-Agents can:
- minimise disclosure of surveillance-sensitive evidence,
- reject invalid control attempts,
- support bounded trust-state transitions,
- isolate suspicious components safely,
- preserve auditability and policy discipline.
