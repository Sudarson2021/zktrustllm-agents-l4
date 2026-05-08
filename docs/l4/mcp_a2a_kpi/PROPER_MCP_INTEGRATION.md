# Proper MCP Integration for Level 4

## Motivation

The Level 4 architecture requires both A2A and MCP.

A2A provides compact inter-agent reference exchange. MCP provides structured access to the authenticated context behind those references.

## Implemented MCP Role

The current MCP server is a read-only context/tool access layer over the deployed Level 4 blockchain state.

It exposes tools for:

- retrieving AUTH_V2.2 decisions,
- retrieving A2A references,
- checking reference validity,
- verifying that an A2A reference matches its source AUTH_V2.2 decision,
- summarising available Level 4 KPIs.

## Relationship to A2A

A2A sends compact reference values such as:

- `referenceId`,
- `sourceDecisionId`,
- `capabilityId`,
- `policyClassHash`,
- `traceCommitment`,
- `cidHash`,
- `proofRef`.

MCP then resolves and verifies those values against blockchain-authenticated state.

## Measured MCP Result

The current MCP test produced:

- listed MCP tools: 5
- successful MCP tool calls: 5/5
- MCP context retrieval success rate: 1.0
- average tool invocation latency: 29.711 ms
- maximum tool invocation latency: 39.757 ms
- reference bundle validity: true
- reference bundle verification latency: 32.298 ms

## Evaluation Benefit

This allows the Level 4 system to measure:

- MCP context retrieval success rate,
- MCP tool invocation latency,
- MCP reference-bundle verification latency,
- A2A reference validity,
- proof-backed policy admissibility,
- compact-reference coordination correctness.

## Security Boundary

The first MCP server is intentionally read-only.

This avoids unsafe automatic actuation. Write-capable MCP actions such as rekeying, isolating, or modifying policy are future work and should require authorization, capability checks, and proof-bound policy controls.
