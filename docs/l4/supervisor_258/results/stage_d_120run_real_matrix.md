# Stage D-real: 120-run n8n real-variant matrix evidence

Generated: 2026-06-28T02:24:39
Batch ID: `20260628_001404`
Total records: 120
Passed records: 120
Failed records: 0
Git hash: `c91333a2937819d44eb6e50be7593fbfe91b497b`

## Variant summary

| Variant | Runs | Passed | Mean ms | p50 ms | p95 ms | Min | Max | Command |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| full-l4 | 40 | 40 | 123575.7 | 122331.5 | 150125 | 98276 | 152177 | `bash scripts/reproduce_all.sh` |
| no-ipfs | 40 | 40 | 2008.3 | 2023.0 | 2084 | 1844 | 2171 | `bash scripts/baselines/run_no_ipfs.sh` |
| oracle-only | 40 | 40 | 1865.9 | 1655.5 | 4096 | 1484 | 4182 | `bash scripts/baselines/run_oracle_only.sh` |

## Variant/profile summary

| Variant | Profile | Runs | Passed | Mean ms | p50 ms | p95 ms | Min | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full-l4 | clean | 10 | 10 | 104056.0 | 104153.5 | 108021 | 98276 | 110101 |
| full-l4 | delay | 10 | 10 | 115223.5 | 114837.5 | 119926 | 109569 | 121592 |
| full-l4 | delay_jitter | 10 | 10 | 130026.6 | 129861.0 | 135232 | 123071 | 136087 |
| full-l4 | delay_jitter_loss | 10 | 10 | 144996.8 | 144424.0 | 150786 | 137683 | 152177 |
| no-ipfs | clean | 10 | 10 | 2056.3 | 2048.0 | 2084 | 2028 | 2097 |
| no-ipfs | delay | 10 | 10 | 1964.9 | 1970.5 | 2009 | 1889 | 2054 |
| no-ipfs | delay_jitter | 10 | 10 | 2052.3 | 2039.5 | 2069 | 2014 | 2171 |
| no-ipfs | delay_jitter_loss | 10 | 10 | 1959.8 | 1975.0 | 2025 | 1844 | 2048 |
| oracle-only | clean | 10 | 10 | 1627.4 | 1644.5 | 1687 | 1484 | 1724 |
| oracle-only | delay | 10 | 10 | 2603.0 | 1667.5 | 4157 | 1490 | 4182 |
| oracle-only | delay_jitter | 10 | 10 | 1603.1 | 1632.5 | 1692 | 1486 | 1696 |
| oracle-only | delay_jitter_loss | 10 | 10 | 1630.2 | 1657.0 | 1690 | 1494 | 1708 |

## Claim boundary

This Stage D-real run is a local n8n-orchestrated 120-run matrix over the three implemented real variants: full-l4, oracle-only, and no-ipfs. It covers four labelled profiles and ten repeats per variant/profile cell.

The evidence supports local workflow repeatability, executable baseline comparison, and profile-labelled orchestration robustness for the implemented variants.

It should not be described as a 240-run six-variant ablation study, production O-RAN deployment, measured packet-level network impairment benchmark, public-chain benchmark, or real media-plane QoE validation unless additional experiments add those missing measurement sources.

Raw per-run manifests are stored under `runtime_artifacts/n8n/runs/`, and the compact manifest index is stored as `stage_d_120run_manifest_index.jsonl`.
