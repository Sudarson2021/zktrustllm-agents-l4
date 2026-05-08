# Level 4 Results Tables

## Table 1: MCP/A2A Agent KPIs

| KPI | Result | Interpretation |
|---|---:|---|
| MCP tools listed | 5 | MCP server exposes structured context/tool access |
| MCP successful tool calls | 5/5 | All tested MCP calls succeeded |
| MCP context retrieval success rate | 1.0 | Authenticated context retrieval was successful in the controlled setup |
| MCP average tool invocation latency | 29.711 ms | Bounded tool-access overhead |
| MCP maximum tool invocation latency | 39.757 ms | Worst observed MCP tool latency in the test |
| MCP bundle verification latency | 32.298 ms | Reference-bundle verification overhead |
| A2A reference validity | true | Compact reference was valid |
| A2A reference registration gas | 440349 | On-chain reference registration cost |
| Raw A2A message size | 1239 bytes | Representative expanded context payload |
| Reference A2A message size | 680 bytes | Compact reference payload |
| Coordination compression gain | 45.12% | Reference mode reduces inter-agent message size |

## Table 2: AUTH_V2.3 Reference-Bound Proof Result

| Item | Result |
|---|---:|
| Decision ID | 1 |
| Proof output | 1 |
| Policy admissibility flag | 1 |
| Trust state | 3 |
| Action class | 3 |
| Gas used | 671779 |
| Reference context hash | 13910625391943923264185798681093047247761942130660331693554321209527545263200 |
| Coordination session ID | 12343182470573131826629052782455202610058935007512043442711127914022411250849 |

## Table 3: Negative-Security Results

| Test category | Cases tested | Cases passed | Rejection rate |
|---|---:|---:|---:|
| AUTH_V2.3 tampered proof/input cases | 7 | 7 | 1.0 |
| MCP/A2A invalid-context cases | 4 | 4 | 1.0 |

## Table 4: Network KPI Telemetry-Emulation Results

| Scenario | Control bytes | Response time ms | Jitter ms | Packet loss % | Containment ms | Service interruption ms | Recovery ms | Proof-governed | Reference-bound |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| baseline_direct_agent | 420 | 89.6 | 5.58 | 0.442 | 127.6 | 187.6 | 266 | false | false |
| l4_raw_context | 1239 | 150.098 | 5.14 | 0.394 | 151.2 | 171.2 | 241.2 | true | false |
| l4_ref_mcp_a2a | 680 | 127.111 | 4.28 | 0.312 | 135 | 143.8 | 214.2 | true | true |

## Table 5: L4 Reference Mode Improvements

| Comparison | Result |
|---|---:|
| L4-ref control-message reduction vs L4-raw | 45.12% |
| L4-ref control-response change vs L4-raw | -15.31% |
| L4-ref jitter change vs L4-raw | -16.73% |
| L4-ref packet-loss change vs L4-raw | -20.81% |
| L4-ref service-interruption change vs baseline | -23.35% |

## Note

The network KPI results are deterministic telemetry-emulation values derived from measured MCP/A2A control values. They are not yet live VLC/DTLS/RTP media measurements.
