# Step 108 L4 Repeated-Run Statistics

## Purpose

This step analyses repeated evidence from the Level 4 automation chain, especially Step 96 archived automation runs.

It strengthens the scientific evaluation by showing whether clean RTP and DTLS-RTP telemetry remain stable across repeated agentic automation executions.

## Summary

- Created at: `2026-05-10T12:28:45.074828+00:00`
- Step 96 run directories found: `4`
- Media observations found: `8`
- Overall repeated-run status: **PASS**

## Current Closed-Loop Chain State

| Component | Value |
|---|---|
| step96OverallStatus | `PASS` |
| step97Decision | `GENERATE_SUPERVISOR_REPORT` |
| step98Status | `EXECUTED_PASS` |
| step100Status | `EXECUTED_PASS` |
| step101EntryCount | `14` |
| step101FinalLedgerHash | `0db58b3f2c09e530c280dc6cd795a53df54e3337b4a46aa9c70fe6ea166c2567` |
| step102IpfsStatus | `IPFS_ADD_PASS` |
| step102IpfsCid | `QmW7VeYs3fP5kk92JstT8tAEkQytgseH4SfhKRpcSwU112` |
| step103GasUsed | `320095` |
| step104OverallStatus | `PASS` |
| step105OverallStatus | `EXECUTED_PASS` |

## Aggregate Media Statistics

| Mode | Observations | Pass rate % | Bitrate mean kbps | Loss mean % | Jitter mean ms |
|---|---:|---:|---:|---:|---:|
| dtls_rtp | 4 | 100.0 | 102.17 | 0.0 | 0.975089 |
| plain_rtp | 4 | 100.0 | 833.605 | 0.0 | 0.29405 |

## Observation-Level Evidence

| Run ID | Mode | Packets | Bitrate kbps | Loss % | Jitter ms | Status |
|---|---|---:|---:|---:|---:|---|
| 20260509_160118 | plain_rtp | 2328 | 833.605 | 0.0 | 0.242929 | PASS |
| 20260509_160118 | dtls_rtp | 769 | 102.17 | 0.0 | 1.040521 | PASS |
| 20260509_161848 | plain_rtp | 2328 | 833.605 | 0.0 | 0.308886 | PASS |
| 20260509_161848 | dtls_rtp | 769 | 102.17 | 0.0 | 0.953029 | PASS |
| 20260509_163127 | plain_rtp | 2328 | 833.605 | 0.0 | 0.287971 | PASS |
| 20260509_163127 | dtls_rtp | 769 | 102.17 | 0.0 | 0.942776 | PASS |
| 20260509_164507 | plain_rtp | 2328 | 833.605 | 0.0 | 0.336413 | PASS |
| 20260509_164507 | dtls_rtp | 769 | 102.17 | 0.0 | 0.96403 | PASS |

## Research Meaning

Step 108 provides repeatability evidence for the Level 4 automation workflow. The project has already demonstrated policy-gated execution, KPI decisioning, remediation, audit-ledger construction, IPFS anchoring, and on-chain validation. This step adds stability evidence by analysing repeated clean-media snapshots produced by prior automation runs.

This is important for journal evaluation because it helps show that the automation pipeline is not a single successful demonstration, but a repeatable scientific workflow.

## Boundary

This step does not rerun experiments, use sudo, push code, deploy contracts, or modify prior evidence. It reads existing artifacts and produces repeated-run statistics.

## Generated Files

- Summary JSON: `results/l4_repeated_run_statistics/repeated_run_statistics_summary.json`
- Observation CSV: `results/l4_repeated_run_statistics/repeated_run_media_observations.csv`
- Aggregate CSV: `results/l4_repeated_run_statistics/repeated_run_aggregate_statistics.csv`
- Markdown: `docs/l4/repeated_run_statistics/L4_REPEATED_RUN_STATISTICS.md`
- PDF: `results/l4_report_pdf/zktrustllm_l4_repeated_run_statistics_steps96_107.pdf`
