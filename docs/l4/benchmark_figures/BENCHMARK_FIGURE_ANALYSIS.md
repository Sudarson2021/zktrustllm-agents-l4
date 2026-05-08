# Level 4 Benchmark Figure Analysis

## Purpose

This document explains the benchmark figures added in Step 85.

The figures align with the supervisor feedback requesting clearer result visualisation for agent KPIs and network/control KPIs over the Level 4 approach.

The current figures are deterministic benchmark/emulation figures derived from the Step 80-84 workflow. They are intended for supervisor alignment and journal-figure preparation. They are not yet live DTLS/RTP/VLC measurements.

## Figure 5.3: Agent Scaling of Level 4 Coordination

Figure 5.3 evaluates A2A/MCP coordination latency as the number of agents increases.

The compared methods are:

- Direct agent baseline
- Heuristic policy agent
- L4 raw-context
- Proposed L4-ref MCP/A2A

The purpose is to show that raw-context coordination becomes increasingly expensive as the number of agents increases, while compact reference-based MCP/A2A coordination scales more efficiently.

The proposed L4-ref MCP/A2A method reduces average coordination latency compared with the L4 raw-context method because agents exchange compact references rather than expanded context payloads.

## Figure 5.4: Decision Utility across Agent Positions

Figure 5.4 evaluates decision utility across representative agent positions.

The compared methods are:

- Direct agent baseline
- Heuristic policy agent
- L4 raw-context
- Proposed L4-ref MCP/A2A

The agent positions represent the multi-agent decision path, such as telemetry, trust, policy, action, and audit roles.

The proposed L4-ref MCP/A2A method shows higher and more stable decision utility because it combines:

- authenticated blockchain state,
- MCP context resolution,
- compact A2A reference exchange,
- AUTH_V2.3 reference-bound proof verification,
- negative-security rejection guarantees.

## Research Interpretation

The two figures support the following claim:

The proposed L4 MCP/A2A reference-bound method improves the security-efficiency balance of multi-agent coordination. It reduces raw coordination overhead compared with raw-context exchange while preserving proof-governed policy admissibility and authenticated state verification.

## Important Boundary

These figures should be labelled as deterministic benchmark/emulation results until replaced with live DTLS/RTP/VLC telemetry.

For the journal paper, they can be presented as preliminary controlled evaluation figures, followed by a future-work statement that live multimedia/network measurements will replace or extend them.
