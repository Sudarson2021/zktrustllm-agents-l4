# Expected Results for MCP/A2A over Level 4

## Summary

The Level 4 approach introduces moderate proof and blockchain verification overhead, but improves trust-aware coordination, reduces redundant inter-agent payload exchange, and strengthens policy-governed action control.

## Result 1: L4-ref reduces A2A message size

L4-ref exchanges compact authenticated references instead of full raw decision/evidence payloads.

Measured/derived output:

- Raw A2A message bytes: `1239`
- Reference A2A message bytes: `680`
- Coordination compression gain: `45.12%`

Interpretation:

Reference-based A2A reduces repeated payload exchange and supports more scalable inter-agent coordination.

## Result 2: L4-ref preserves verifiability

The A2A reference is valid only when it matches the authenticated AUTH_V2.2 on-chain decision.

Measured output:

- `referenceId = 1`
- `sourceDecisionId = 1`
- `valid = true`
- `bundleValid = true`

Interpretation:

Agent B can verify the compact reference through authenticated blockchain state instead of receiving the full raw payload.

## Result 3: MCP enables structured context access

The MCP server exposes authenticated Level 4 context as structured tools.

Measured output:

- MCP tools listed: `5`
- MCP successful tool calls: `5/5`
- MCP context retrieval success rate: `1.0`
- MCP average tool invocation latency: `29.711 ms`
- MCP maximum tool invocation latency: `39.757 ms`
- MCP bundle verification latency: `32.298 ms`

Interpretation:

MCP provides a structured and measurable tool-access layer for retrieving decisions, references, validity state, and bundle verification results.

## Result 4: AUTH_V2.2 improves trust-aware admissibility

The accepted decision binds:

- agent identity,
- capability ID,
- policy class,
- action class,
- context hash,
- trace commitment,
- expiry bucket,
- policy admissibility flag,
- trust state.

Measured output:

- `actionClass = 3`
- `trustState = 3`
- `policyAdmissibilityFlag = 1`
- policy admissibility observed: `true`
- trust-aware action observed: `true`

Interpretation:

The AUTH_V2.2 proof-backed path confirms that the accepted action is bound to the expected trust-state semantics.

## Result 5: Level 4 adds bounded control-path overhead

The A2A reference registration requires additional gas and control-path verification.

Measured output:

- A2A reference registration gas: `440349`

Interpretation:

This overhead is appropriate for an audit/control-plane path, but not for the real-time media path. Therefore, DTLS/RTP/multicast media delivery remains off-chain.

## Result 6: Remaining network KPIs require telemetry integration

The current implementation measures MCP/A2A control and verification KPIs.

The next telemetry wrapper should measure:

- control response time,
- jitter during control events,
- packet loss during orchestration,
- containment time,
- service continuity impact,
- recovery time.
