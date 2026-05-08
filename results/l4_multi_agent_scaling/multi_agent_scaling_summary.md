# Step 87 Multi-Agent Scaling Telemetry Summary

> These results are repeated semi-live MCP/A2A control-plane measurements across increasing agent counts. They are not yet live VLC/DTLS/RTP media telemetry.

## Scenario Summary

| Mode | Agents | Repetitions | Success rate | Avg total latency ms | Avg per-agent latency ms | Avg bytes | Avg agents/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_direct_agent | 5 | 3 | 1.0 | 0.005 | 0.001 | 826 | 1147116.384 |
| baseline_direct_agent | 10 | 3 | 1.0 | 0.005 | 0.001 | 1651 | 1843783.338 |
| baseline_direct_agent | 15 | 3 | 1.0 | 0.006 | 0.0 | 2481 | 2494223.615 |
| baseline_direct_agent | 20 | 3 | 1.0 | 0.009 | 0.0 | 3311 | 2199026.953 |
| baseline_direct_agent | 25 | 3 | 1.0 | 0.013 | 0.001 | 4141 | 1970542.069 |
| l4_raw_context | 5 | 3 | 1.0 | 338.424 | 67.685 | 17412.333 | 14.787 |
| l4_raw_context | 10 | 3 | 1.0 | 696.929 | 69.693 | 34824.667 | 14.362 |
| l4_raw_context | 15 | 3 | 1.0 | 1180.903 | 78.727 | 52242 | 12.778 |
| l4_raw_context | 20 | 3 | 1.0 | 1401.078 | 70.054 | 69655.667 | 14.279 |
| l4_raw_context | 25 | 3 | 1.0 | 1717.749 | 68.71 | 87078 | 14.559 |
| l4_ref_mcp_a2a | 5 | 3 | 1.0 | 158.581 | 31.716 | 391 | 31.572 |
| l4_ref_mcp_a2a | 10 | 3 | 1.0 | 322.859 | 32.286 | 781 | 31.026 |
| l4_ref_mcp_a2a | 15 | 3 | 1.0 | 490.131 | 32.675 | 1176 | 30.645 |
| l4_ref_mcp_a2a | 20 | 3 | 1.0 | 634.776 | 31.739 | 1571 | 31.521 |
| l4_ref_mcp_a2a | 25 | 3 | 1.0 | 817.638 | 32.706 | 1966 | 30.577 |

## L4 Reference Improvements over L4 Raw-Context

| Agents | Latency reduction | Message reduction | Throughput gain |
|---:|---:|---:|---:|
| 5 | 53.14% | 97.75% | 113.51% |
| 10 | 53.67% | 97.76% | 116.03% |
| 15 | 58.5% | 97.75% | 139.83% |
| 20 | 54.69% | 97.74% | 120.75% |
| 25 | 52.4% | 97.74% | 110.02% |

## Research Meaning

The multi-agent scaling telemetry shows how the proposed L4-ref MCP/A2A coordination path behaves as the number of agents increases. It provides measured evidence that compact reference exchange reduces control-message size and improves coordination efficiency compared with raw-context exchange.
