# Level 4 Network KPI Telemetry Results

## Purpose

This document summarises the Step 83 network-facing KPI evaluation for the Level 4 MCP/A2A reference-bound coordination workflow.

## Important Note

The current results are deterministic telemetry-emulation results derived from measured MCP/A2A control-plane values.

They are not yet live VLC/DTLS/RTP media measurements.

The purpose is to provide a reproducible network-KPI layer before connecting the workflow to real multimedia telemetry.

## Evaluated Scenarios

Three scenarios are compared:

1. `baseline_direct_agent`
   - direct agent control without blockchain/MCP/A2A reference verification.

2. `l4_raw_context`
   - Level 4 proof-governed mode where agents exchange expanded raw context.

3. `l4_ref_mcp_a2a`
   - Level 4 reference mode where A2A exchanges compact references and MCP resolves authenticated blockchain context.

## KPI Categories

The network-facing KPIs include:

- control message size,
- control-plane overhead,
- control response time,
- jitter during control event,
- packet loss during orchestration,
- containment time,
- service interruption,
- recovery time.

## Security Coupling

The network KPI result is connected with the previous security evidence:

- AUTH_V2.3 tampered rejection rate = 1.0
- MCP/A2A invalid-context rejection rate = 1.0

Therefore, the L4-ref mode is not only smaller in control-message size than L4-raw, but also proof-governed and reference-bound.

## Result Files

- JSON result: `results/l4_network_kpis/network_kpi_summary.json`
- CSV result: `results/l4_network_kpis/network_kpi_summary.csv`
- Markdown summary: `results/l4_network_kpis/network_kpi_summary.md`

## Research Meaning

This step turns the MCP/A2A Level 4 design into a network-facing evaluation framework.

The result supports the claim that compact authenticated references can reduce inter-agent control-message overhead while preserving proof-governed trust, policy, and reference-binding semantics.

## Next Step

The next experimental step is to replace deterministic telemetry-emulation values with real DTLS/RTP/VLC or network-emulator logs.
