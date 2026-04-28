# Primary Evaluation Scenario

## Scenario Title
Secure multimedia streaming over 5G-Advanced edge/MEC networks

## Purpose
This scenario is the main evaluation environment for the ZKTrustLLM-Agents architecture.

It is used to show why privacy-preserving trust verification and agentic orchestration are needed in multimedia systems where:
- service continuity matters,
- trust decisions must be made quickly,
- sensitive evidence should not be fully disclosed,
- transport and media delivery must remain standards-based.

---

## 1. Environment

The target environment consists of:
- multimedia applications generating or consuming video streams,
- edge / MEC nodes providing local processing and adaptation,
- a 5G-Advanced network carrying traffic and control connectivity,
- end devices receiving or transmitting multimedia content,
- an application/control plane that reasons over trust state and policy.

The actual media path remains on standard communication and security protocols such as RTP, SRTP, DTLS, or QUIC.

---

## 2. Actors

The main actors are:
- end users / user devices
- multimedia service providers
- edge / MEC nodes
- control-plane agents
- trust and policy services
- smart-contract-backed trust anchoring components

---

## 3. Assets

The main protected assets are:
- multimedia session continuity
- trust state of the service path
- authorization scope for control actions
- integrity of policy-triggered actions
- privacy-sensitive evidence and trace data
- auditability of trust-relevant decisions

---

## 4. Threats

Representative threats include:
- unauthorized agent or control request
- invalid or expired capability use
- compromised edge behaviour
- contradictory trust evidence
- replayed control messages
- policy-violating mitigation requests
- attempts to disclose sensitive evidence beyond allowed scope

---

## 5. Trust Decisions

This scenario evaluates whether the system can correctly decide:
- whether a context package is trustworthy enough for progression,
- whether an agent request is authorized,
- whether a policy action is admissible,
- whether the service path should remain trusted,
- whether the path should be degraded, restricted, isolated, or quarantined.

---

## 6. Policy Actions

The bounded mitigation classes in this scenario are:
- keep
- rekey
- rotate
- isolate
- quarantine

These actions are chosen by the control plane, while media transport itself remains unchanged.

---

## 7. Why This Scenario Is Important

This is the strongest primary scenario because it combines:
- low-latency multimedia delivery,
- distributed trust boundaries,
- sensitive operational evidence,
- need for auditable decisions,
- need for bounded automated orchestration.

It closely matches the intended journal positioning for privacy-preserving multimedia trust management over 5G-Advanced systems.

---

## 8. Evaluation Questions

The primary scenario should answer the following questions:
1. Can valid trust-relevant decisions be verified without exposing raw sensitive evidence?
2. Can invalid or tampered control/proof paths be rejected reliably?
3. Can bounded policy actions be selected correctly from trust-state changes?
4. Can the system preserve standards-based media delivery while adding trust orchestration?
5. Can decisions be anchored for audit without moving media traffic onto blockchain?

---

## 9. Metrics

Core evaluation metrics for this scenario are:
- decision latency
- proof verification overhead
- policy-action correctness
- unauthorized request rejection rate
- containment speed
- blast-radius reduction
- trust-state recovery time

---

## 10. Baseline Comparison Direction

This scenario should later be compared against:
- transport/security-only baseline
- current L2 trust-verification baseline
- partial L4 control-plane baseline
- full L4 agentic trust-orchestration baseline

---

## 11. Expected Outcome

The expected result is that ZKTrustLLM-Agents can:
- preserve the normal multimedia data path,
- verify trust-relevant properties with minimal disclosure,
- reject invalid requests and tampered paths,
- select bounded policy actions correctly,
- anchor trust events for later audit and review.
