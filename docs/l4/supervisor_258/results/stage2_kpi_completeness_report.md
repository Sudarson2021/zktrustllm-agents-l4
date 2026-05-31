# Stage 2 KPI Completeness Report

Total clean records: 240

| KPI | Non-null records | Coverage | Interpretation |
|---|---:|---:|---|
| prover_time_ms | 160/240 | 66.67% | Populated for ablation rows where prover is intentionally not invoked; direct prover logs still needed for full ZK rows. |
| anchor_gas | 240/240 | 100.00% | Populated from Stage 3 isolated ledger micro-benchmark runtime hook. |
| rtp_jitter_ms | 240/240 | 100.00% | Configured impairment-profile KPI; replace later with packet-capture evidence. |
| rtp_loss_pct | 240/240 | 100.00% | Configured impairment-profile KPI; replace later with packet-capture evidence. |
| dtls_rtp_jitter_ms | 240/240 | 100.00% | Configured impairment-profile KPI; replace later with packet-capture evidence. |
| dtls_rtp_loss_pct | 240/240 | 100.00% | Configured impairment-profile KPI; replace later with packet-capture evidence. |
| reason_latency_ms | 240/240 | 100.00% | Populated from Stage 3 deterministic policy-reasoning probe. |
| replay_rejected | 240/240 | 100.00% | Populated from Stage 3 negative-security runtime hook. |
| zero_anchor_rejected | 240/240 | 100.00% | Populated from Stage 3 negative-security runtime hook. |
| unauthorized_submitter_rejected | 240/240 | 100.00% | Populated for RBAC-only runs where the current-API test confirms non-oracle rejection. |
| post_auto_score_gas | 240/240 | 100.00% | Extracted from Hardhat logs where available. |
| hardhat_passing_tests | 240/240 | 100.00% | Extracted from Hardhat logs where available. |
| hardhat_failing_tests | 200/240 | 83.33% | Extracted from Hardhat logs where available. |

## Scientific interpretation

The Stage 2 extraction layer extends the n8n workflow-validation dataset into a scientific KPI-tracking dataset. It currently provides complete configured media impairment coverage, Hardhat gas/test KPIs, and RBAC unauthorized-submitter rejection evidence. Stage 3 now provides direct runtime-hook evidence for anchor gas, reasoning latency, replay rejection, zero-anchor rejection, and unauthorized-submitter rejection. Missing values are still intentionally preserved for full ZK prover timing where direct prover logs are not yet available.

## Reviewer-safety note

Configured media-profile values should not be described as packet-capture measurements. They are scenario-control parameters until replaced by tshark, VLC, tc/netem, or O-RAN telemetry measurements.
