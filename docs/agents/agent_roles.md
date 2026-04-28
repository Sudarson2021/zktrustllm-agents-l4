# ZKTrustLLM-Agents Initial Agent Roles

## Purpose
This document freezes the first three agents for the L4 control plane.

The implementation scope at this stage is intentionally limited to:
- EdgeTelemetryAgent
- TrustRiskAgent
- PolicyLKHAgent

These three agents are sufficient to establish:
- context collection,
- trust/risk interpretation,
- bounded policy action selection.

---

# 1. EdgeTelemetryAgent

## 1.1 Goal
Summarise local multicast, network, service, and control-path context at the edge without exposing unnecessary raw data.

## 1.2 Core responsibilities
- collect trust-relevant local observations
- summarise network and multicast state
- package evidence-relevant features
- emit trace-linked context summaries
- support commitment-bound downstream verification

## 1.3 Inputs
- multicast membership state
- session/network state
- control events
- local anomaly indicators
- policy context
- optional user/service orchestration requests

## 1.4 Outputs
- context summary
- evidence hash / payload hash
- context hash
- trace reference / traceCID
- anomaly hint bundle
- bounded telemetry summary

## 1.5 Allowed capabilities
- local context collection
- evidence summarisation
- bounded metadata generation
- signed gateway message submission

## 1.6 Trust-sensitive actions
- emit signed context package
- request escalation if anomaly threshold is crossed
- request additional verification when evidence is inconsistent

## 1.7 Failure conditions
- repeated malformed evidence output
- unsigned or stale gateway submissions
- scope violation
- contradictory telemetry patterns beyond threshold

## 1.8 Audit outputs
- trace-linked summary
- payload hash
- anomaly summary
- timestamped control event reference

---

# 2. TrustRiskAgent

## 2.1 Goal
Assess whether verified evidence is sufficient, trustworthy, and policy-admissible before an action is permitted.

## 2.2 Core responsibilities
- consume verified evidence summaries
- interpret trust state and anomaly signals
- determine risk level
- decide whether action progression is safe
- issue bounded trust/risk recommendations

## 2.3 Inputs
- verified trust properties
- capability validity status
- context summary
- anomaly indicators
- policy context
- prior trust state

## 2.4 Outputs
- risk classification
- trust recommendation
- admissibility result
- escalation / restriction recommendation
- confidence summary

## 2.5 Allowed capabilities
- read bounded trust summaries
- read verified authorization status
- emit signed trust/risk result
- request policy evaluation

## 2.6 Trust-sensitive actions
- classify state as trusted / degraded / suspect / restricted
- request secondary verification
- recommend isolation or quarantine readiness
- block forward progression when trust is insufficient

## 2.7 Failure conditions
- inconsistent result relative to verified evidence
- repeated unjustified escalation
- unauthorized policy read/request
- stale decision relative to current context hash

## 2.8 Audit outputs
- risk decision
- admissibility decision
- trust-state transition hint
- explanation reference linked to traceCID

---

# 3. PolicyLKHAgent

## 3.1 Goal
Convert verified trust/risk outputs into bounded multicast/control actions without redesigning the media plane.

## 3.2 Core responsibilities
- map trust state and policy context to allowed mitigation classes
- enforce bounded LKH action selection
- preserve separation between control logic and media delivery path

## 3.3 Inputs
- trust/risk recommendation
- policy class
- current mitigation state
- capability validity
- trust-state category

## 3.4 Outputs
- keep
- rekey
- rotate
- isolate
- quarantine
- escalation metadata

## 3.5 Allowed capabilities
- read policy matrix
- request bounded mitigation action
- emit signed action decision
- trigger policy event anchoring

## 3.6 Trust-sensitive actions
- choose action class
- reject disallowed action class
- request subgroup isolation
- request quarantine when policy threshold is crossed

## 3.7 Failure conditions
- action selected outside allowed policy class
- capability scope mismatch
- mitigation action emitted without verified trust basis
- invalid transition from trust state to action class

## 3.8 Audit outputs
- selected action class
- policy rule identifier
- mitigation event summary
- trace-bound justification reference

---

# 4. Common Agent Requirements

## 4.1 Identity requirements
Every agent must:
- be registered
- possess valid key material
- operate under explicit role metadata
- present a valid capability for the active task

## 4.2 Messaging requirements
Every agent message must be:
- signed
- scoped to a task
- tied to a context hash
- policy-class aware
- freshness-checked by the secure gateway

## 4.3 Governance requirements
Every agent action must remain:
- auditable
- bounded by capability
- explainable through trace-linked metadata
- policy-compliant at decision time

---

# 5. Initial Agent-to-Agent Interaction Pattern

## 5.1 EdgeTelemetryAgent -> TrustRiskAgent
Purpose:
- provide context summary and trust-relevant evidence features

## 5.2 TrustRiskAgent -> PolicyLKHAgent
Purpose:
- provide admissibility result and risk-aware decision recommendation

## 5.3 PolicyLKHAgent -> Control/Execution Layer
Purpose:
- emit bounded mitigation class for execution without altering the media-plane design

---

# 6. Initial Non-goals
At this stage the agents do not:
- replace RTP, DTLS, QUIC, or transport logic
- inspect or transport bulk media on-chain
- bypass gateway validation
- consume unrestricted raw evidence by default

---

# 7. Status
This document freezes the first three agents as the initial L4 control-plane set.
Future agent additions must be justified against this baseline rather than added ad hoc.
