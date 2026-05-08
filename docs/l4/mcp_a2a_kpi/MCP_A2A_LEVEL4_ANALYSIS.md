# MCP/A2A Analysis for Level 4 Proof-Governed Agent Coordination

## 1. Purpose

This document analyses MCP/A2A over the Level 4 ZKTrustLLM-Agents approach using agent KPIs, network KPIs, and related measured or derived results.

The Level 4 approach is defined as:

> Proof-governed multi-agent coordination over blockchain-anchored authenticated shared state.

## 2. Level 4 Architecture

The implemented Level 4 workflow is:

1. Agent A creates an AUTH_V2.2 Groth16 proof-backed decision.
2. The decision is stored on-chain.
3. Agent A registers a compact A2A reference using `A2AReferenceRegistry`.
4. Agent B receives the compact reference.
5. Agent B uses MCP tools to retrieve and verify the authenticated blockchain context behind that reference.
6. Agent B accepts the decision only if the reference bundle matches the source AUTH_V2.2 decision.

## 3. MCP Role

MCP is used as the structured context/tool-access layer.

In this project, the proper read-only MCP server exposes tools for:

- retrieving AUTH_V2.2 decisions,
- retrieving A2A references,
- checking A2A reference validity,
- verifying that a reference matches its source decision,
- summarising Level 4 MCP/A2A KPIs.

Therefore, MCP affects:

- context retrieval success,
- context retrieval latency,
- reference-bundle verification latency,
- structured interoperability,
- tool-access correctness.

## 4. A2A Role

A2A is used as the inter-agent coordination layer.

In this project, A2A supports reference-based coordination using:

- `referenceId`,
- `sourceDecisionId`,
- `capabilityId`,
- `policyClassHash`,
- `contextHash`,
- `traceCommitment`,
- `cidHash`,
- `proofRef`.

Therefore, A2A affects:

- inter-agent coordination overhead,
- reference reuse,
- message-size reduction,
- agent consistency,
- auditability of coordination.

## 5. Blockchain and ZK Role

Blockchain provides authenticated shared state.

AUTH_V2.2 provides proof-governed admissibility by binding:

- agent identity,
- capability ID,
- policy class,
- action class,
- context hash,
- trace commitment,
- expiry bucket,
- policy admissibility flag,
- trust state.

## 6. Evaluation Question

Can MCP/A2A-based agent orchestration, when anchored to blockchain-authenticated shared state and proof-governed policy admissibility, improve trust-aware decision quality while keeping network-control overhead bounded?

## 7. Evaluation Modes

| Mode | Description |
|---|---|
| Baseline-AI | Agent-only decision logic without blockchain-authenticated state |
| Level-2 | AI consumes blockchain-authenticated state but without closed-loop A2A reference coordination |
| L4-raw | Agents exchange full raw decision/evidence/context payloads |
| L4-ref | Agents exchange compact authenticated references and resolve context through MCP |

## 8. Current Implemented Result

The current prototype demonstrates the L4-ref mode.

Measured result:

| Metric | Value |
|---|---|
| AUTH_V2.2 decision count | 1 |
| A2A reference count | 1 |
| A2A reference validity | true |
| A2A reference registration gas | 440349 |
| MCP tools listed | 5 |
| MCP successful tool calls | 5/5 |
| MCP context retrieval success rate | 1.0 |
| MCP average tool invocation latency | 29.711 ms |
| MCP maximum tool invocation latency | 39.757 ms |
| MCP reference-bundle validity | true |
| MCP bundle verification latency | 32.298 ms |

## 9. Research Interpretation

The result shows that Agent B can use MCP to resolve and verify the authenticated blockchain context behind an A2A reference.

This supports the Level 4 claim:

> A2A provides compact inter-agent reference exchange, MCP provides structured access to authenticated blockchain state, blockchain acts as shared authenticated memory, and ZK proofs provide policy-governed admissibility.

## 10. Practical Boundary

The blockchain and MCP/A2A workflow operates on the control/audit path only.

Live media remains off-chain and should continue to use the DTLS/RTP/multicast media path. Blockchain stores decisions, references, commitments, and proof-verification-related state, not raw media.
