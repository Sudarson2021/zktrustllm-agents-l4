# Step 86 Semi-Live Control-Plane Telemetry Summary

> These results measure actual local MCP/A2A control-plane timings. They are not yet live VLC/DTLS/RTP media telemetry.

## Scenario Summary

| Mode | Runs | Success rate | Avg response ms | P50 ms | P95 ms | Jitter std ms | Avg control bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_direct_agent | 20 | 1.0 | 0.001 | 0.001 | 0.001 | 0.0 | 159.55 |
| l4_raw_context | 20 | 1.0 | 72.793 | 72.974 | 77.039 | 3.119 | 3477.25 |
| l4_ref_mcp_a2a | 20 | 1.0 | 34.918 | 35.556 | 36.155 | 1.406 | 72.55 |

## L4 Reference Mode Improvements

- L4-ref latency reduction vs L4 raw-context: 52.03%
- L4-ref control-message reduction vs L4 raw-context: 97.91%

## Research Meaning

The semi-live telemetry validates the MCP/A2A control-plane path using actual local tool invocation timings. It strengthens the Step 83 deterministic network KPI analysis by replacing part of the emulated values with measured control-loop timings.
