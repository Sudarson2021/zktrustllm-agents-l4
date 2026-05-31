# n8n-Based Scientific Evaluation Design

## Purpose

n8n is used as a reproducible workflow orchestrator for the ZKTrustLLM-Agents L4 evaluation. It coordinates experiment execution, but does not replace the actual scientific tools.

## Tool Boundary

| Layer | Tool |
|---|---|
| Workflow orchestration | n8n |
| Smart-contract evaluation | Hardhat |
| ZK proof evaluation | ZoKrates / Groth16 verifier path |
| Formal verification | TLA+ / TLC |
| Evidence storage | IPFS / CID-compatible evidence |
| KPI aggregation | Python scripts |
| Paper artifacts | CSV, Markdown, LaTeX snippets, figures |

## Evaluation Variants

1. full_l4
2. no_zk
3. oracle_only
4. rbac_only
5. no_ipfs
6. no_policy_gate

## Impairment Profiles

1. clean_baseline
2. delay_20ms
3. delay_20ms_jitter_5ms
4. delay_30ms_jitter_10ms_loss_1pct

## Minimum Repeats

Each variant-profile pair should be repeated 10 times.

Total ablation records:

6 variants x 4 profiles x 10 repeats = 240 records.

## Required Output per Run

Each run must produce:

- run_config.json
- git_commit.txt
- raw.log
- hardhat_test.log where applicable
- kpis.json
- evidence.sha256
- paper-ready CSV row

## Scientific Reporting

The paper should report mean, median, standard deviation, p50, p95, pass/fail count, rejection rate, and overhead percentage against baseline.
