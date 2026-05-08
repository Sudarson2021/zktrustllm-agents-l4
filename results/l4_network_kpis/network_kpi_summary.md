# Level 4 Network KPI Telemetry-Emulation Summary

> These are deterministic telemetry-emulation results derived from measured MCP/A2A control values. They are not yet live VLC/DTLS/RTP measurements.

## Measured Inputs

- Raw A2A message bytes: 1239
- Reference A2A message bytes: 680
- MCP average tool invocation latency: 29.711 ms
- MCP bundle verification latency: 32.298 ms
- AUTH_V2.3 gas used: 671779
- AUTH_V2.3 tampered rejection rate: 1.0
- MCP/A2A invalid-context rejection rate: 1.0

## Scenario Results

| Scenario | Control bytes | Response ms | Jitter ms | Packet loss % | Containment ms | Service interruption ms | Recovery ms | Proof-governed | Reference-bound |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| baseline_direct_agent | 420 | 89.6 | 5.58 | 0.442 | 127.6 | 187.6 | 266 | False | False |
| l4_raw_context | 1239 | 150.098 | 5.14 | 0.394 | 151.2 | 171.2 | 241.2 | True | False |
| l4_ref_mcp_a2a | 680 | 127.111 | 4.28 | 0.312 | 135 | 143.8 | 214.2 | True | True |

## Key Interpretation

- L4-ref control-message reduction versus L4-raw: 45.12%
- L4-ref control-response change versus L4-raw: -15.31%
- L4-ref jitter change versus L4-raw: -16.73%
- L4-ref packet-loss change versus L4-raw: -20.81%
- L4-ref service-interruption change versus baseline: -23.35%

## Research Meaning

The Level 4 reference mode reduces inter-agent control-message size compared with raw-context coordination while preserving proof-governed and reference-bound decision semantics.
