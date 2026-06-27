# n8n Scientific Novelty Matrix for ZKTrustLLM-Agents L4

## Core Scientific Position

n8n is not claimed as the security mechanism. Instead, n8n is used as the reproducible scientific orchestration layer that repeatedly executes, records, validates, and exports evidence from the proposed ZKTrustLLM-Agents L4 framework.

## Novelty Matrix

| Scientific gap | Conventional weakness | n8n-based improvement | Measurable output |
|---|---|---|---|
| Manual demo execution | Results may depend on screenshots and manual commands. | Every experiment is workflow-triggered and timestamped. | run_id, timestamp, Git commit, logs. |
| Weak repeatability | One-off results are hard to defend. | Repeated runs across variants and impairment profiles. | mean, p50, p95, std, pass/fail rate. |
| Unclear ablation | ZK/IPFS/RBAC effects are not isolated. | Full, No-ZK, No-IPFS, Oracle-only, RBAC-only, and No-policy-gate variants. | ablation CSV and paper table. |
| Weak threat validation | Threats are described but not systematically replayed. | Replay, zero-anchor, unauthorized submitter, mutated proof, and unsafe action tests are executed. | attack outcome matrix. |
| Missing formal-verification evidence | Table observations are descriptive. | n8n triggers TLA+ and Hardhat invariant checks. | formal verification table. |
| Weak O-RAN KPI link | Agent/security results may look disconnected from network KPIs. | Network KPIs are joined with agent decision, proof, and anchor outputs. | network-agent-trust joined dataset. |
| Weak traceability | Figures/tables may not map to raw evidence. | Raw logs, JSON, CSV, Markdown tables, and LaTeX snippets are stored. | reviewer-verifiable evidence bundle. |

## Paper Claim Enabled by n8n

The n8n evaluation layer converts ZKTrustLLM-Agents L4 from a functional prototype into a reproducible scientific testbed by orchestrating repeated experiments, ablations, formal checks, threat-response tests, and paper-ready evidence generation under one auditable workflow.

## Recommended Experimental Scale

| Group | Variants | Profiles | Repeats | Total records |
|---|---:|---:|---:|---:|
| Full L4 | 1 | 4 | 10 | 40 |
| Ablation | 6 | 4 | 10 | 240 |
| Access control | 5 | 1 | 10 | 50 |
| Threat response | 7 | 1 | 10 | 70 |
| Consensus/test modes | 4 | 1 | 10 | 40 |

Minimum journal-ready target: 240 structured ablation records plus formal-verification and threat-response evidence.
