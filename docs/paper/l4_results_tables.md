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

## Table 6: Figure 5.3 Agent-Scaling Benchmark Summary

| Method | Mean coordination latency ms | Interpretation |
|---|---:|---|
| Direct agent baseline | 111.8 | Lowest simple control overhead but no proof governance or authenticated reference binding |
| Heuristic policy agent | 143.2 | Local heuristic decision path without blockchain-authenticated context verification |
| L4 raw-context | 186.4 | Proof-governed but larger raw context exchange increases coordination cost |
| Proposed L4-ref MCP/A2A | 144.2 | Reference-bound, proof-governed coordination with lower latency than L4 raw-context |

## Table 7: Figure 5.4 Decision-Utility Benchmark Summary

| Method | Mean decision utility | Interpretation |
|---|---:|---|
| Direct agent baseline | 0.696 | Direct agent decision without authenticated state or proof governance |
| Heuristic policy agent | 0.736 | Rule-based local policy decision |
| L4 raw-context | 0.840 | Stronger proof-governed decision path but with larger context exchange |
| Proposed L4-ref MCP/A2A | 0.926 | Highest decision utility due to compact references, MCP context verification, and AUTH_V2.3 binding |

## Figure References

- Figure 5.3 source files:
  - `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.png`
  - `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.pdf`
  - `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.svg`

- Figure 5.4 source files:
  - `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.png`
  - `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.pdf`
  - `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.svg`

Note: These figures are deterministic benchmark/emulation figures. They are not yet live DTLS/RTP/VLC measurements.
