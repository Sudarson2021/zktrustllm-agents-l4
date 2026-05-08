# Artifact Mapping (Paper ↔ Code)

Entry point:
  scripts/reproduce_all.sh

Output directory:
  artifacts/out/

Baselines:
- Oracle-only (no ZK):
    scripts/baselines/run_oracle_only.sh
    artifacts/out/baseline_oracle_only/
- No-IPFS evidence (local store):
    scripts/baselines/run_no_ipfs.sh
    artifacts/out/baseline_no_ipfs/

Scoring / reputation:
- Spec: docs/scoring.md
- Implementation: update this file later to point to the exact source file/function used in your repo.

Evidence vs media delivery (important):
- Live media delivery: DTLS/RTP/multicast plane
- Evidence storage: IPFS (CID) + on-chain commitments for auditability

## L4 AUTH_V1 Groth16 artifact path

Primary runner:
- `scripts/l4/run_auth_v1_groth16_repro.sh`

Summary note:
- `docs/l4/AUTH_V1_ARTIFACT_SUMMARY.md`

Key milestone tags:
- `l4-auth-v1-first-real-groth16-submit`
- `l4-auth-v1-groth16-negative-test`
- `l4-auth-v1-groth16-repro`

## L4 A2A Reference-Aware Coordination

This extension implements the supervisor-aligned Level 4 direction: blockchain as authenticated shared memory for multi-agent AI coordination.

Main artifacts:

- Supervisor alignment note: `docs/l4/a2a_reference/SUPERVISOR_ALIGNMENT.md`
- A2A compact reference schema: `schemas/a2a_reference_message.json`
- A2A registry contract: `contracts/l4/A2AReferenceRegistry.sol`
- Deployment script: `scripts/l4/deploy_a2a_reference_registry.js`
- Registry verification script: `scripts/l4/check_a2a_reference_registry.js`
- AUTH_V2.2 decision checker: `scripts/l4/check_auth_v2_2_decisions.js`
- A2A registration demo: `scripts/l4/register_a2a_reference_from_latest_decision.js`
- Demo result: `results/l4_a2a_reference/a2a_reference_latest_decision.json`
- Runtime AUTH_V2.2 proof files: `runtime_artifacts/l4/auth_v2_2/`

Demonstrated result:

- AUTH_V2.2 proof-backed decision count: 1
- A2A reference count: 1
- A2A reference validity: true
- A2A reference registration gas: 440349

Research meaning:

Agent A creates a proof-backed authenticated decision on-chain. Agent B can then rely on a compact reference to that decision instead of receiving the full raw decision, policy, or evidence payload. This demonstrates blockchain-anchored authenticated state as a coordination substrate for Level 4 agent-to-agent interaction.

## L4 Proper MCP Context Server

This section adds a proper read-only MCP server for Level 4 proof-governed coordination.

Main artifacts:

- MCP server: `mcp_l4/server.py`
- MCP server README: `mcp_l4/README.md`
- MCP client test: `scripts/l4/test_mcp_l4_server.py`
- MCP test result: `results/l4_mcp_server/mcp_tool_test_results.json`
- MCP bundle verification result: `results/l4_mcp_server/mcp_reference_bundle_verification.json`
- MCP integration analysis: `docs/l4/mcp_a2a_kpi/PROPER_MCP_INTEGRATION.md`
- MCP Python requirements: `requirements-l4-mcp.txt`

Measured result:

- MCP tools listed: 5
- successful MCP tool calls: 5/5
- MCP context retrieval success rate: 1.0
- average tool invocation latency: 29.711 ms
- maximum tool invocation latency: 39.757 ms
- reference bundle validity: true
- reference bundle verification latency: 32.298 ms

Research meaning:

A2A provides compact inter-agent reference exchange. MCP provides structured access to the authenticated blockchain context behind those references. The implemented MCP tools allow an agent to retrieve and verify AUTH_V2.2 decisions and A2A references without directly receiving full raw decision or evidence payloads.

## L4 MCP/A2A KPI Analysis

This section extends the proper MCP server and A2A reference-aware coordination prototype with detailed KPI analysis.

Main artifacts:

- MCP/A2A Level 4 analysis: `docs/l4/mcp_a2a_kpi/MCP_A2A_LEVEL4_ANALYSIS.md`
- KPI table: `docs/l4/mcp_a2a_kpi/KPI_TABLE.md`
- Expected results: `docs/l4/mcp_a2a_kpi/EXPECTED_RESULTS.md`
- Network KPI plan: `docs/l4/mcp_a2a_kpi/NETWORK_KPI_PLAN.md`
- KPI analysis script: `scripts/l4/analyze_mcp_a2a_level4_kpis.py`
- KPI JSON result: `results/l4_mcp_a2a_kpi/kpi_summary.json`
- KPI CSV result: `results/l4_mcp_a2a_kpi/kpi_summary.csv`
- KPI Markdown summary: `results/l4_mcp_a2a_kpi/kpi_summary.md`

Measured/derived result:

- MCP tools listed: 5
- MCP successful tool calls: 5/5
- MCP context retrieval success rate: 1.0
- MCP average tool invocation latency: 29.711 ms
- MCP maximum tool invocation latency: 39.757 ms
- MCP reference-bundle validity: true
- MCP bundle verification latency: 32.298 ms
- A2A reference validity: true
- A2A reference registration gas: 440349
- Raw A2A message size: 1239 bytes
- Reference A2A message size: 680 bytes
- Coordination compression gain: 45.12%

Research meaning:

This analysis directly addresses the Level 4 MCP/A2A evaluation requirement. MCP provides structured context/tool access. A2A provides compact inter-agent coordination. Blockchain provides authenticated shared state. AUTH_V2.2 provides proof-governed admissibility. Network KPIs are defined for the next control/media telemetry experiment.

## L4 AUTH_V2.3 Reference-Bound Proof

This section adds AUTH_V2.3, a reference-bound proof relation for Level 4 MCP/A2A coordination.

Main artifacts:

- AUTH_V2.3 circuit: `circuits/auth_v2_3.zok`
- AUTH_V2.3 relation documentation: `docs/zk/auth_v2_3_reference_binding.md`
- AUTH_V2.3 generated verifier: `contracts/l4/generated/AuthV2_3Verifier.sol`
- AUTH_V2.3 decision attestor: `contracts/l4/DecisionAttestorAuthV2_3.sol`
- AUTH_V2.3 payload builder: `scripts/l4/build_auth_v2_3_reference_payload.py`
- AUTH_V2.3 verifier debug check: `scripts/l4/debug_auth_v2_3_verifier.js`
- AUTH_V2.3 deployment script: `scripts/l4/deploy_auth_v2_3_wrapper.js`
- AUTH_V2.3 submit script: `scripts/l4/submit_auth_v2_3_reference_bound.js`
- AUTH_V2.3 runtime artifacts: `runtime_artifacts/l4/auth_v2_3/`
- AUTH_V2.3 result: `results/l4_auth_v2_3/reference_bound_decision.json`

Measured result:

- AUTH_V2.3 decision ID: `1`
- Proof output: `1`
- Policy admissibility flag: `1`
- Trust state: `3`
- Action class: `3`
- AUTH_V2.3 gas used: `671779`
- Reference context hash: `13910625391943923264185798681093047247761942130660331693554321209527545263200`
- Coordination session ID: `12343182470573131826629052782455202610058935007512043442711127914022411250849`

Research meaning:

AUTH_V2.3 extends AUTH_V2.2 by binding the proof-backed decision to an MCP/A2A reference context. This moves the Level 4 design from reference-after-decision to reference-bound proof-governed multi-agent coordination.

## L4 Step 82 MCP/A2A Negative Security Tests

This section adds negative-security evidence for the Level 4 proof-governed MCP/A2A coordination workflow.

Main artifacts:

- AUTH_V2.3 negative test script: `scripts/l4/test_auth_v2_3_negative_cases.js`
- AUTH_V2.3 negative result: `results/l4_auth_v2_3_negative/auth_v2_3_negative_summary.json`
- MCP/A2A negative test script: `scripts/l4/test_mcp_a2a_negative_cases.py`
- MCP/A2A negative result: `results/l4_mcp_a2a_security/mcp_a2a_negative_summary.json`
- Negative-security documentation: `docs/l4/mcp_a2a_security/NEGATIVE_SECURITY_RESULTS.md`
- Step 82 summary script: `scripts/l4/summarize_step82_negative_security.py`
- Step 82 summary: `results/l4_mcp_a2a_security/step82_negative_security_summary.md`

Measured result:

- AUTH_V2.3 valid proof path accepted
- AUTH_V2.3 tampered proof/input rejection rate: 1.0
- MCP/A2A invalid-context rejection rate: 1.0

Research meaning:

These tests show that the Level 4 design accepts valid reference-bound proof paths while rejecting tampered proof inputs, malformed verifier inputs, invalid decision lookups, and invalid A2A reference contexts.

## L4 Step 83 Network KPI Telemetry Results

This section adds a network-facing KPI evaluation layer for the Level 4 MCP/A2A reference-bound coordination workflow.

Main artifacts:

- Network KPI script: `scripts/l4/simulate_mcp_a2a_network_kpis.py`
- Network KPI JSON result: `results/l4_network_kpis/network_kpi_summary.json`
- Network KPI CSV result: `results/l4_network_kpis/network_kpi_summary.csv`
- Network KPI Markdown summary: `results/l4_network_kpis/network_kpi_summary.md`
- Network KPI documentation: `docs/l4/network_kpi/NETWORK_KPI_TELEMETRY_RESULTS.md`

Measured/derived input values:

- Raw A2A message bytes: 1239
- Reference A2A message bytes: 680
- MCP average tool invocation latency: 29.711 ms
- MCP bundle verification latency: 32.298 ms
- AUTH_V2.3 gas used: 671779
- AUTH_V2.3 tampered rejection rate: 1.0
- MCP/A2A invalid-context rejection rate: 1.0

Research meaning:

This step turns the Level 4 MCP/A2A workflow into a network-facing KPI evaluation. It compares baseline direct-agent control, L4 raw-context coordination, and L4 compact-reference coordination. The result supports the claim that compact authenticated references reduce inter-agent control-message overhead while preserving proof-governed and reference-bound decision semantics.

Important boundary:

The current results are deterministic telemetry-emulation results, not live VLC/DTLS/RTP measurements. The next step is to replace the emulated telemetry values with real media/network logs.

## L4 Step 84 Journal-Ready Evaluation Write-Up

This section adds paper-ready write-up material for the Level 4 MCP/A2A reference-bound proof-governed coordination workflow.

Main artifacts:

- Main evaluation section: `docs/paper/l4_mcp_a2a_evaluation_section.md`
- Results tables: `docs/paper/l4_results_tables.md`
- Supervisor alignment summary: `docs/paper/l4_supervisor_alignment_summary.md`
- Limitations and next steps: `docs/paper/l4_limitations_and_next_steps.md`

Research meaning:

This step converts the Level 4 implementation and evaluation evidence into a journal/report-ready narrative. It connects the supervisor comments with the implemented architecture, agent KPIs, network KPIs, AUTH_V2.3 reference-bound proof, negative-security results, and telemetry-emulation results.

## L4 Step 85 Benchmark Result Figures

This section adds benchmark result figures aligned with supervisor feedback.

Main artifacts:

- Benchmark figure generator: `scripts/l4/generate_l4_benchmark_figures.py`
- Figure 5.3 CSV: `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.csv`
- Figure 5.3 PNG: `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.png`
- Figure 5.3 PDF: `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.pdf`
- Figure 5.3 SVG: `results/l4_benchmark_figures/figure_5_3_agent_scaling_latency.svg`
- Figure 5.4 CSV: `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.csv`
- Figure 5.4 PNG: `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.png`
- Figure 5.4 PDF: `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.pdf`
- Figure 5.4 SVG: `results/l4_benchmark_figures/figure_5_4_decision_utility_positions.svg`
- Figure summary JSON: `results/l4_benchmark_figures/benchmark_figure_summary.json`
- Figure analysis: `docs/l4/benchmark_figures/BENCHMARK_FIGURE_ANALYSIS.md`

Research meaning:

Figure 5.3 shows agent-scaling coordination latency. Figure 5.4 shows decision utility across agent positions. Together, they visually support the claim that the proposed L4-ref MCP/A2A method improves coordination efficiency and decision quality compared with raw-context and heuristic benchmark methods, while preserving proof-governed and reference-bound semantics.

Important boundary:

These figures are deterministic benchmark/emulation figures and are not yet live DTLS/RTP/VLC measurements.

## L4 Step 86 Semi-Live Control-Plane Telemetry

This section adds semi-live measured MCP/A2A control-plane telemetry.

Main artifacts:

- Telemetry runner: `scripts/l4/run_l4_semi_live_control_telemetry.py`
- Event-level telemetry CSV: `results/l4_live_telemetry/semi_live_control_events.csv`
- Telemetry summary JSON: `results/l4_live_telemetry/semi_live_control_summary.json`
- Telemetry summary Markdown: `results/l4_live_telemetry/semi_live_control_summary.md`
- Figure 5.5 PNG/PDF/SVG: `results/l4_live_telemetry/figure_5_5_semi_live_control_latency.*`
- Figure 5.6 PNG/PDF/SVG: `results/l4_live_telemetry/figure_5_6_semi_live_control_summary.*`
- Documentation: `docs/l4/live_telemetry/SEMI_LIVE_CONTROL_TELEMETRY.md`

Measured result:

- baseline direct-agent average control response: 0.001 ms
- L4 raw-context average control response: 72.793 ms
- L4-ref MCP/A2A average control response: 34.918 ms
- L4-ref latency reduction vs raw-context: 52.03%
- L4-ref control-message reduction vs raw-context: 97.91%

Research meaning:

This step moves the evaluation from deterministic network KPI emulation toward actual measured MCP/A2A control-plane telemetry. It repeatedly measures baseline direct-agent control, L4 raw-context coordination, and proposed L4-ref MCP/A2A coordination.

Boundary:

These are semi-live control-plane measurements and are not yet live VLC/DTLS/RTP media-plane measurements.

## L4 Step 87 Multi-Agent Scaling Telemetry

This section adds repeated semi-live MCP/A2A scaling telemetry across increasing agent counts.

Main artifacts:

- Scaling runner: `scripts/l4/run_l4_multi_agent_scaling_telemetry.py`
- Event-level scaling CSV: `results/l4_multi_agent_scaling/multi_agent_scaling_events.csv`
- Scaling summary JSON: `results/l4_multi_agent_scaling/multi_agent_scaling_summary.json`
- Scaling summary Markdown: `results/l4_multi_agent_scaling/multi_agent_scaling_summary.md`
- Figure 5.7 PNG/PDF/SVG: `results/l4_multi_agent_scaling/figure_5_7_multi_agent_scaling_latency.*`
- Figure 5.8 PNG/PDF/SVG: `results/l4_multi_agent_scaling/figure_5_8_multi_agent_control_bytes.*`
- Figure 5.9 PNG/PDF/SVG: `results/l4_multi_agent_scaling/figure_5_9_multi_agent_throughput.*`
- Documentation: `docs/l4/multi_agent_scaling/MULTI_AGENT_SCALING_TELEMETRY.md`

Measured result:

- 5 agents: L4-ref latency reduction 53.14%, message reduction 97.75%, throughput gain 113.51%
- 10 agents: L4-ref latency reduction 53.67%, message reduction 97.76%, throughput gain 116.03%
- 15 agents: L4-ref latency reduction 58.50%, message reduction 97.75%, throughput gain 139.83%
- 20 agents: L4-ref latency reduction 54.69%, message reduction 97.74%, throughput gain 120.75%
- 25 agents: L4-ref latency reduction 52.40%, message reduction 97.74%, throughput gain 110.02%

Research meaning:

This step evaluates how the proposed L4-ref MCP/A2A coordination path behaves as the number of agents increases. It provides measured scaling evidence for compact reference exchange compared with raw-context coordination.

Boundary:

These are semi-live MCP/A2A control-plane scaling measurements and are not yet live VLC/DTLS/RTP media-plane measurements.

## L4 Step 88 Journal Technical Report PDF

This section adds a supervisor-ready technical report PDF covering the Level 4 workflow from Step 77 to Step 87.

Main artifacts:

- Report builder: `scripts/l4/build_l4_technical_report_pdf.py`
- Report README: `docs/report/README.md`
- Markdown report source: `docs/report/zktrustllm_l4_technical_report_steps77_87.md`
- PDF report: `results/l4_report_pdf/zktrustllm_l4_technical_report_steps77_87.pdf`
- Report Python requirements: `requirements-l4-report.txt`

Report coverage:

- Step 77: A2A reference-aware coordination
- Step 79: Proper MCP context server
- Step 80: MCP/A2A KPI analysis
- Step 81: AUTH_V2.3 reference-bound proof
- Step 82: Negative-security tests
- Step 83: Network KPI telemetry-emulation
- Step 84: Journal-ready evaluation write-up
- Step 85: Benchmark result figures
- Step 86: Semi-live MCP/A2A control-plane telemetry
- Step 87: Multi-agent scaling telemetry

Research meaning:

This report converts the implementation, KPI analysis, negative-security evidence, benchmark figures, semi-live telemetry, and multi-agent scaling results into a single technical document for supervisor review and future journal writing.

Boundary:

The report clearly states that current measurements are blockchain/MCP/A2A control-plane measurements and are not yet live VLC/DTLS/RTP media-plane measurements.

## L4 Step 89 Live RTP Media-Plane Telemetry

This section adds live RTP media-plane telemetry to the Level 4 evaluation workflow.

Main artifacts:

- RTP media telemetry runner: `scripts/l4/run_live_rtp_media_telemetry.py`
- RTP packet event CSV: `results/l4_live_rtp_media/rtp_packet_events.csv`
- RTP media summary JSON: `results/l4_live_rtp_media/rtp_media_summary.json`
- RTP media summary Markdown: `results/l4_live_rtp_media/rtp_media_summary.md`
- Figure 5.10 PNG/PDF/SVG: `results/l4_live_rtp_media/figure_5_10_live_rtp_jitter.*`
- Figure 5.11 PNG/PDF/SVG: `results/l4_live_rtp_media/figure_5_11_live_rtp_bitrate.*`
- Figure 5.12 PNG/PDF/SVG: `results/l4_live_rtp_media/figure_5_12_live_rtp_sequence_progress.*`
- Documentation: `docs/l4/live_rtp_media/LIVE_RTP_MEDIA_TELEMETRY.md`

Measured result:

- Received RTP packets: 2328
- Expected RTP packets: 2328
- Lost packets: 0
- Packet loss: 0.0%
- Average bitrate: 833.605 kbps
- Average jitter component: 0.229169 ms
- P50 jitter component: 0.069357 ms
- Maximum jitter component: 4.163946 ms

Research meaning:

This step moves the project from control-plane-only MCP/A2A telemetry toward live media-plane validation by measuring RTP packet continuity, jitter, bitrate, and packet loss.

Boundary:

This is live RTP media-plane telemetry over localhost. It is not yet DTLS-secured. The next step should add DTLS-secured RTP validation.

## L4 Step 90 DTLS-Wrapped RTP Media-Plane Validation

This section adds DTLS-wrapped RTP media-plane validation.

Main artifacts:

- DTLS/RTP proxy source: `dtls_rtp/dtls_rtp_proxy.c`
- DTLS/RTP build script: `dtls_rtp/build.sh`
- DTLS/RTP telemetry runner: `scripts/l4/run_dtls_rtp_media_telemetry.py`
- DTLS/RTP jitter recomputation script: `scripts/l4/recompute_dtls_rtp_arrival_jitter.py`
- DTLS/RTP packet event CSV: `results/l4_dtls_rtp_media/dtls_rtp_packet_events.csv`
- DTLS/RTP summary JSON: `results/l4_dtls_rtp_media/dtls_rtp_media_summary.json`
- DTLS/RTP summary Markdown: `results/l4_dtls_rtp_media/dtls_rtp_media_summary.md`
- DTLS/RTP figures: `results/l4_dtls_rtp_media/figure_5_13_dtls_rtp_jitter.*`
- Plain-vs-DTLS comparison figures: `results/l4_dtls_rtp_media/figure_5_14_plain_vs_dtls_packet_loss.*`, `results/l4_dtls_rtp_media/figure_5_15_plain_vs_dtls_bitrate.*`
- Documentation: `docs/l4/dtls_rtp_media/DTLS_RTP_MEDIA_VALIDATION.md`

Measured result:

- DTLS handshake completed successfully.
- Recovered RTP packets: 769.
- Packet loss: 0.0%.
- Average recovered bitrate: 102.17 kbps.

Research meaning:

This step moves the Level 4 workflow from plain RTP media-plane telemetry to secured DTLS-wrapped RTP media-plane validation.
