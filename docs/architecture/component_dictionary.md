# ZKTrustLLM-Agents Component Dictionary

## Purpose
This document freezes the initial component dictionary for the L4 ZKTrustLLM-Agents architecture.

It is used to:
1. stabilise the final architecture figure,
2. define where each component resides,
3. clarify data, control, and audit interactions,
4. support later paper writing and implementation mapping.

The architecture is organised into four logical planes:
- Application & Agentic Control Plane
- Trust & Verification Plane
- Audit & Trust Anchoring Plane
- Communication & Media Delivery Plane

---

# 1. Application & Agentic Control Plane

## 1.1 LLM Reasoning Engine
- **Plane:** Application & Agentic Control Plane
- **Purpose:** Interprets policy, contextual state, and verified trust outputs to support bounded orchestration decisions.
- **Reads:** verified trust summaries, policy context, system objectives, bounded evidence summaries
- **Writes:** reasoning outputs, decision recommendations, coordination hints
- **Interfaces:** Orchestrator Agent, MCP/A2A Interface Layer

## 1.2 Orchestrator Agent
- **Plane:** Application & Agentic Control Plane
- **Purpose:** Coordinates workflow progression, task delegation, and agent-to-agent sequencing.
- **Reads:** reasoning outputs, trust state, task state, policy context
- **Writes:** task assignments, coordination messages, action requests
- **Interfaces:** LLM Reasoning Engine, Trust Evaluation Agent, Policy Enforcement Agent, MCP/A2A Interface Layer

## 1.3 Trust Evaluation Agent
- **Plane:** Application & Agentic Control Plane
- **Purpose:** Interprets verified outcomes and trust-state changes before policy action is allowed.
- **Reads:** verified trust properties, anomaly indicators, evidence sufficiency summaries
- **Writes:** trust/risk interpretation, admissibility recommendation
- **Interfaces:** Orchestrator Agent, Trust Manager

## 1.4 Policy Enforcement Agent
- **Plane:** Application & Agentic Control Plane
- **Purpose:** Converts admissible decisions into bounded control actions on the application/control path.
- **Reads:** policy recommendation, trust/risk outcome, capability status
- **Writes:** enforceable control actions, mitigation triggers, policy execution events
- **Interfaces:** Orchestrator Agent, Capability / Authorization Manager, Media Security Stack

## 1.5 MCP / A2A Interface Layer
- **Plane:** Application & Agentic Control Plane
- **Purpose:** Supports bounded tool/context access and structured inter-agent coordination.
- **Reads:** approved context, policy-approved resource access, bounded tool requests
- **Writes:** structured agent messages, context exchange, coordination metadata
- **Interfaces:** LLM Reasoning Engine, Orchestrator Agent, secure gateway

---

# 2. Trust & Verification Plane

## 2.1 Trust Manager
- **Plane:** Trust & Verification Plane
- **Purpose:** Aggregates trust-relevant outputs and maintains current trust state.
- **Reads:** verified proof outcomes, anomaly signals, capability status, policy admissibility state
- **Writes:** trust-state updates, confidence summaries, control-plane trust outputs
- **Interfaces:** Trust Evaluation Agent, ZK Proof Engine, Capability / Authorization Manager, Blockchain Trust Anchor

## 2.2 ZK Proof Engine
- **Plane:** Trust & Verification Plane
- **Purpose:** Generates or verifies privacy-preserving proofs for authorization and policy-compliance conditions.
- **Reads:** evidence commitments, public inputs, witness material, capability context
- **Writes:** verifier-ready proof outputs, verification results, proof metadata
- **Interfaces:** Evidence Processor, Trust Manager, Smart Contracts

## 2.3 Evidence Processor
- **Plane:** Trust & Verification Plane
- **Purpose:** Converts raw evidence into commitments, hashes, and policy-relevant derived features.
- **Reads:** media/edge events, control events, trust-relevant telemetry, anomaly features
- **Writes:** commitments, context hashes, payload hashes, trace references, evidence summaries
- **Interfaces:** ZK Proof Engine, IPFS / Evidence Store

## 2.4 Capability / Authorization Manager
- **Plane:** Trust & Verification Plane
- **Purpose:** Validates short-lived least-privilege capabilities and authorization scope.
- **Reads:** agent identity, task scope, capability metadata, policy class
- **Writes:** validity decisions, scope checks, authorization status
- **Interfaces:** Trust Manager, Policy Enforcement Agent, secure gateway, capability contract layer

---

# 3. Audit & Trust Anchoring Plane

## 3.1 Blockchain Trust Anchor
- **Plane:** Audit & Trust Anchoring Plane
- **Purpose:** Provides immutable anchoring of trust events, proof outcomes, and policy-relevant decisions.
- **Reads:** trust-state events, proof results, policy events, decision summaries
- **Writes:** append-only audit entries, anchored trust records
- **Interfaces:** Trust Manager, Smart Contracts

## 3.2 Smart Contracts
- **Plane:** Audit & Trust Anchoring Plane
- **Purpose:** Persist verifier outcomes, agent decisions, capability events, and policy-related audit state.
- **Reads:** proof submissions, capability updates, trust events, anomaly events
- **Writes:** on-chain verifier results, decision attestations, capability records, audit metadata
- **Interfaces:** ZK Proof Engine, Blockchain Trust Anchor, contract clients

## 3.3 IPFS / Evidence Store
- **Plane:** Audit & Trust Anchoring Plane
- **Purpose:** Stores off-path evidence artefacts for cold-path audit and traceability.
- **Reads:** evidence bundles, anomaly bundles, trace artefacts, rollback records
- **Writes:** CID-linked evidence references, retrievable audit artefacts
- **Interfaces:** Evidence Processor, Blockchain Trust Anchor

---

# 4. Communication & Media Delivery Plane

## 4.1 Multimedia Applications
- **Plane:** Communication & Media Delivery Plane
- **Purpose:** Produce and consume multimedia services such as video streaming, AR/VR, and V2X media exchange.
- **Reads:** application inputs, control decisions, media content
- **Writes:** media streams, application events, service-level evidence
- **Interfaces:** Media Security Stack

## 4.2 Media Security Stack
- **Plane:** Communication & Media Delivery Plane
- **Purpose:** Carries actual multimedia traffic using standards-based security and transport mechanisms.
- **Reads:** media packets, session state, bounded control actions
- **Writes:** secured traffic flow, transport/security state
- **Interfaces:** Multimedia Applications, Edge / MEC Nodes

## 4.3 Edge / MEC Nodes
- **Plane:** Communication & Media Delivery Plane
- **Purpose:** Perform low-latency local processing, adaptation, and trust-relevant observation at the edge.
- **Reads:** media/session state, network state, local events
- **Writes:** processed traffic, local telemetry, edge evidence
- **Interfaces:** Media Security Stack, 5G-Advanced Network, Evidence Processor

## 4.4 5G-Advanced Network
- **Plane:** Communication & Media Delivery Plane
- **Purpose:** Provides the transport substrate for media and control connectivity.
- **Reads:** secured traffic, mobility/network state
- **Writes:** end-to-end delivery, network telemetry, routing state
- **Interfaces:** Edge / MEC Nodes, End Devices

## 4.5 End Devices
- **Plane:** Communication & Media Delivery Plane
- **Purpose:** Receive, transmit, or interact with media and service-level control actions.
- **Reads:** delivered media, policy-enforced service behaviour
- **Writes:** user/device state, session activity, device-side evidence
- **Interfaces:** 5G-Advanced Network

---

# 5. Design Principles Frozen at This Stage

1. Agentic AI is used for trust orchestration and policy reasoning, not as a replacement for transport.
2. Blockchain is used for auditability and trust anchoring, not for high-throughput media transfer.
3. Zero-knowledge proofs minimise data disclosure, but are not the media transmission mechanism.
4. Actual delivery remains on TCP/IP-based and IETF-aligned media/security paths such as RTP, SRTP, DTLS, and QUIC.
5. Trust evidence is processed off the hot media path and exposed upward only through bounded, verified summaries.
