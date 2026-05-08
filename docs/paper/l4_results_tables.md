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

## Table 8: Step 86 Semi-Live Control Telemetry Summary

| Mode | Runs | Success rate | Avg response ms | P50 ms | P95 ms | Jitter std ms | Avg control bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_direct_agent | 20 | 1.0 | 0.001 | 0.001 | 0.001 | 0.0 | 159.55 |
| l4_raw_context | 20 | 1.0 | 72.793 | 72.974 | 77.039 | 3.119 | 3477.25 |
| l4_ref_mcp_a2a | 20 | 1.0 | 34.918 | 35.556 | 36.155 | 1.406 | 72.55 |

## Table 9: Step 86 L4 Reference Improvement

| Metric | Result |
|---|---:|
| L4-ref latency reduction vs L4 raw-context | 52.03% |
| L4-ref control-message reduction vs L4 raw-context | 97.91% |

Figure source files:

- `results/l4_live_telemetry/figure_5_5_semi_live_control_latency.png`
- `results/l4_live_telemetry/figure_5_5_semi_live_control_latency.pdf`
- `results/l4_live_telemetry/figure_5_5_semi_live_control_latency.svg`
- `results/l4_live_telemetry/figure_5_6_semi_live_control_summary.png`
- `results/l4_live_telemetry/figure_5_6_semi_live_control_summary.pdf`
- `results/l4_live_telemetry/figure_5_6_semi_live_control_summary.svg`

Note: These are semi-live MCP/A2A control-plane measurements, not live VLC/DTLS/RTP media measurements.

## Table 10: Step 87 Multi-Agent Scaling Improvement Summary

| Agents | L4-ref latency reduction vs raw | L4-ref message reduction vs raw | L4-ref throughput gain vs raw |
|---:|---:|---:|---:|
| 5 | 53.14% | 97.75% | 113.51% |
| 10 | 53.67% | 97.76% | 116.03% |
| 15 | 58.50% | 97.75% | 139.83% |
| 20 | 54.69% | 97.74% | 120.75% |
| 25 | 52.40% | 97.74% | 110.02% |

## Table 11: Step 87 Multi-Agent Scaling Result Files

| Artifact | Path |
|---|---|
| Event-level CSV | `results/l4_multi_agent_scaling/multi_agent_scaling_events.csv` |
| Summary JSON | `results/l4_multi_agent_scaling/multi_agent_scaling_summary.json` |
| Summary Markdown | `results/l4_multi_agent_scaling/multi_agent_scaling_summary.md` |
| Figure 5.7 latency PNG | `results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.png` |
| Figure 5.8 control bytes PNG | `results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.png` |
| Figure 5.9 throughput PNG | `results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.png` |

Note: These are semi-live MCP/A2A control-plane scaling measurements, not live VLC/DTLS/RTP media measurements.

## Table 12: Step 89 Live RTP Media-Plane Telemetry Results

| KPI | Result | Interpretation |
|---|---:|---|
| Capture duration | 25 seconds | Live RTP capture window |
| RTP endpoint | 127.0.0.1:5004 | Local RTP media-plane test |
| Received RTP packets | 2328 | Packets captured by Python RTP receiver |
| Expected RTP packets | 2328 | Packets expected from RTP sequence continuity |
| Lost packets | 0 | No sequence-gap loss observed |
| Packet loss | 0.0% | RTP sequence continuity preserved |
| Average bitrate | 833.605 kbps | RTP media throughput during capture |
| Average jitter component | 0.229169 ms | Low RTP timing variation on localhost |
| P50 jitter component | 0.069357 ms | Median RTP timing variation |
| Maximum jitter component | 4.163946 ms | Largest observed RTP timing deviation |

## Table 13: Step 89 RTP Media-Plane Result Files

| Artifact | Path |
|---|---|
| RTP packet event CSV | `results/l4_live_rtp_media/rtp_packet_events.csv` |
| RTP summary JSON | `results/l4_live_rtp_media/rtp_media_summary.json` |
| RTP summary Markdown | `results/l4_live_rtp_media/rtp_media_summary.md` |
| Figure 5.10 RTP jitter | `results/l4_live_rtp_media/figure_5_10_live_rtp_jitter.png` |
| Figure 5.11 RTP bitrate | `results/l4_live_rtp_media/figure_5_11_live_rtp_bitrate.png` |
| Figure 5.12 RTP sequence progress | `results/l4_live_rtp_media/figure_5_12_live_rtp_sequence_progress.png` |

## Table 14: Step 90 DTLS-Wrapped RTP Media-Plane Results

| KPI | Result | Interpretation |
|---|---:|---|
| DTLS endpoint | 127.0.0.1:4444 | Local DTLS tunnel endpoint |
| Recovered RTP endpoint | 127.0.0.1:5006 | RTP receiver after DTLS recovery |
| Recovered RTP packets | 769 | RTP packets captured after DTLS protection |
| Lost packets | 0 | No sequence-gap loss observed |
| Packet loss | 0.0% | RTP sequence continuity preserved |
| Average bitrate | 102.17 kbps | Recovered DTLS-wrapped RTP throughput |
| Jitter metric | arrival-gap jitter | Avoids H.264 timestamp reordering artefacts |

## Table 15: Step 90 DTLS/RTP Result Files

| Artifact | Path |
|---|---|
| DTLS/RTP event CSV | `results/l4_dtls_rtp_media/dtls_rtp_packet_events.csv` |
| DTLS/RTP summary JSON | `results/l4_dtls_rtp_media/dtls_rtp_media_summary.json` |
| DTLS/RTP summary Markdown | `results/l4_dtls_rtp_media/dtls_rtp_media_summary.md` |
| Figure 5.13 DTLS/RTP jitter | `results/l4_dtls_rtp_media/figure_5_13_dtls_rtp_jitter.png` |
| Figure 5.14 plain vs DTLS packet loss | `results/l4_dtls_rtp_media/figure_5_14_plain_vs_dtls_packet_loss.png` |
| Figure 5.15 plain vs DTLS bitrate | `results/l4_dtls_rtp_media/figure_5_15_plain_vs_dtls_bitrate.png` |

## Table 16: Step 91 Network-Impairment Plain RTP vs DTLS-RTP Result Files

| Artifact | Path |
|---|---|
| Step 91 summary JSON | `results/l4_network_impairment/network_impairment_summary.json` |
| Step 91 summary CSV | `results/l4_network_impairment/network_impairment_summary.csv` |
| Step 91 summary Markdown | `results/l4_network_impairment/network_impairment_summary.md` |
| Figure 5.16 packet loss | `results/l4_network_impairment/figure_5_16_plain_vs_dtls_impairment_packet_loss.png` |
| Figure 5.17 bitrate | `results/l4_network_impairment/figure_5_17_plain_vs_dtls_impairment_bitrate.png` |
| Figure 5.18 arrival-gap jitter | `results/l4_network_impairment/figure_5_18_plain_vs_dtls_impairment_jitter.png` |

Step 91 compares plain RTP and DTLS-wrapped RTP under controlled loopback impairment using Linux `tc netem`. Jitter is reported as arrival-gap jitter to avoid raw RTP timestamp artefacts.
