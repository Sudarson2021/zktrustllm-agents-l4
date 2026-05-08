# Step 86 Semi-Live MCP/A2A Control-Plane Telemetry

## Purpose

This step extends the Level 4 evaluation from deterministic telemetry-emulation to semi-live measured control-plane telemetry.

The experiment measures actual local MCP/A2A control-loop timing for three modes:

1. `baseline_direct_agent`
2. `l4_raw_context`
3. `l4_ref_mcp_a2a`

## What Is Measured

The experiment measures:

- control response time,
- p50 and p95 response time,
- control-loop jitter as latency standard deviation,
- control message size,
- success/failure rate,
- latency reduction of L4-ref compared with L4 raw-context,
- message reduction of L4-ref compared with L4 raw-context.

## Method

The baseline mode performs a local direct policy decision.

The L4 raw-context mode retrieves the source decision, A2A reference, and reference bundle through MCP.

The L4 reference mode sends only a compact reference message and uses MCP to verify the authenticated reference bundle.

## Measured Result

The semi-live telemetry was executed for 20 runs per mode.

Measured summary:

- baseline direct-agent average control response: `0.001 ms`
- L4 raw-context average control response: `72.793 ms`
- L4-ref MCP/A2A average control response: `34.918 ms`
- L4 raw-context p95 response: `77.039 ms`
- L4-ref MCP/A2A p95 response: `36.155 ms`
- L4 raw-context jitter standard deviation: `3.119 ms`
- L4-ref MCP/A2A jitter standard deviation: `1.406 ms`
- L4 raw-context average control-message size: `3477.25 bytes`
- L4-ref MCP/A2A average control-message size: `72.55 bytes`
- L4-ref latency reduction vs raw-context: `52.03%`
- L4-ref control-message reduction vs raw-context: `97.91%`

## Output Files

- Event-level CSV: `results/l4_live_telemetry/semi_live_control_events.csv`
- Summary JSON: `results/l4_live_telemetry/semi_live_control_summary.json`
- Summary Markdown: `results/l4_live_telemetry/semi_live_control_summary.md`
- Figure 5.5: `results/l4_live_telemetry/figure_5_5_semi_live_control_latency.png`
- Figure 5.6: `results/l4_live_telemetry/figure_5_6_semi_live_control_summary.png`

## Research Meaning

This experiment strengthens the Step 83 network KPI analysis by replacing part of the deterministic telemetry-emulation with actual local MCP/A2A tool invocation timings.

It shows that the proposed L4-ref MCP/A2A path has substantially lower measured control-loop latency and control-message size than the L4 raw-context path in the semi-live local setup.

## Boundary

These are semi-live control-plane measurements.

They are not yet live VLC, DTLS, RTP, multicast, or media-plane measurements. The next step should connect this telemetry wrapper to a real multimedia or network-emulator experiment.
