# Step 87 Multi-Agent MCP/A2A Scaling Telemetry

## Purpose

This step evaluates how the Level 4 MCP/A2A control-plane workflow behaves as the number of agents increases.

It extends Step 86 from repeated single-reference control-loop telemetry to multi-agent scaling telemetry.

## Compared Modes

The experiment compares:

1. `baseline_direct_agent`
2. `l4_raw_context`
3. `l4_ref_mcp_a2a`

## Agent Counts

The experiment measures:

- 5 agents
- 10 agents
- 15 agents
- 20 agents
- 25 agents

Each setting is repeated three times.

## Measured KPIs

The experiment measures:

- total coordination latency,
- latency per agent,
- p50 and p95 latency,
- jitter as latency standard deviation,
- control-message size,
- accepted agents per second,
- success rate,
- L4-ref latency reduction compared with L4 raw-context,
- L4-ref message reduction compared with L4 raw-context,
- L4-ref throughput gain compared with L4 raw-context.

## Measured Result Summary

The proposed `l4_ref_mcp_a2a` mode consistently reduces latency and control-message size compared with `l4_raw_context`.

| Agents | L4-ref latency reduction vs raw | L4-ref message reduction vs raw | L4-ref throughput gain vs raw |
|---:|---:|---:|---:|
| 5 | 53.14% | 97.75% | 113.51% |
| 10 | 53.67% | 97.76% | 116.03% |
| 15 | 58.50% | 97.75% | 139.83% |
| 20 | 54.69% | 97.74% | 120.75% |
| 25 | 52.40% | 97.74% | 110.02% |

## Research Meaning

This experiment directly addresses the scalability aspect of the Level 4 design.

The result shows that raw-context coordination becomes expensive as the number of agents increases, while compact reference-based coordination keeps control-message size smaller and improves coordination efficiency.

This supports the supervisor-aligned claim that blockchain-authenticated shared state can simplify inter-agent communication because agents exchange compact references instead of full raw context.

## Output Files

- Event-level CSV: `results/l4_multi_agent_scaling/multi_agent_scaling_events.csv`
- Summary JSON: `results/l4_multi_agent_scaling/multi_agent_scaling_summary.json`
- Summary Markdown: `results/l4_multi_agent_scaling/multi_agent_scaling_summary.md`
- Figure 5.7: `results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.png`
- Figure 5.8: `results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.png`
- Figure 5.9: `results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.png`

## Boundary

These are semi-live MCP/A2A control-plane scaling measurements.

They are not yet live VLC/DTLS/RTP media-plane measurements.
