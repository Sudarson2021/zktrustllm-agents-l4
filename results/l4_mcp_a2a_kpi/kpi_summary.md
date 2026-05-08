# Level 4 MCP/A2A KPI Summary

## Measured Agent KPIs

- MCP tools listed: 5
- MCP successful tool calls: 5/5
- MCP context retrieval success rate: 1.0
- MCP average tool invocation latency: 29.711 ms
- MCP maximum tool invocation latency: 39.757 ms
- MCP bundle verification latency: 32.298 ms
- MCP reference bundle valid: True

## Measured A2A / Proof KPIs

- AUTH_V2.2 source decision ID: 1
- A2A reference ID: 1
- A2A reference valid: True
- A2A reference registration gas: 440349
- Policy admissibility observed: True
- Trust-aware action observed: True

## Derived Message-Size KPIs

- Raw A2A message bytes: 1239
- Reference A2A message bytes: 680
- Coordination compression gain: 45.12%

## Network KPI Status

- Current network-facing KPI output covers control-message size and reference-vs-raw control overhead.
- Jitter, packet loss, containment time, service continuity, and recovery time require the next telemetry wrapper over DTLS/RTP/VLC or emulated network traces.

## Interpretation

The current Level 4 result shows that A2A can exchange a compact authenticated reference, while MCP can retrieve and verify the authenticated blockchain context behind that reference. This supports the claim that blockchain acts as authenticated shared memory, MCP provides structured context/tool access, and A2A provides compact inter-agent coordination.
