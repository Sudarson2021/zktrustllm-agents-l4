# ZKTrustLLM Level 4 MCP Server

This folder contains a proper read-only MCP server for Level 4 proof-governed agent coordination.

## Purpose

The MCP server exposes blockchain-authenticated Level 4 context as MCP tools.

In the Level 4 architecture:

- A2A provides inter-agent compact reference exchange.
- MCP provides structured access to authenticated blockchain context.
- Blockchain acts as authenticated shared state.
- AUTH_V2.2 provides proof-governed policy admissibility.

## Tools

The server exposes:

- `get_auth_v2_2_decision(decision_id)`
- `get_a2a_reference(reference_id)`
- `is_a2a_reference_valid(reference_id)`
- `verify_reference_bundle(reference_id)`
- `get_level4_kpi_summary()`

## Current Demonstration

The current demo uses:

- AUTH_V2.2 decision ID: `1`
- A2A reference ID: `1`
- Reference validity: `true`
- A2A registration gas: `440349`

## Security Position

This MCP server is read-only.

It does not submit blockchain transactions, trigger key rotation, modify policy, or execute network actions. This is intentional for the first research prototype because MCP is used here as a structured context/tool access layer, not as an autonomous actuator.

Write-capable MCP tools are reserved for future work after authorization, sandboxing, and policy controls are added.
