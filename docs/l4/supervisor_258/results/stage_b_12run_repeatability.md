# Stage B: 12-run n8n repeatability evidence

Generated: 2026-06-27T23:46:47
Batch ID: `20260627_233849`
Total records: 12
Passed records: 12
Failed records: 0
Git hash: `30917bc846df503b690a7d0a6846f96a33ceb201`

## Variant summary

| Variant | Runs | Passed | Mean duration ms | Min | Max | Command |
|---|---:|---:|---:|---:|---:|---|
| full-l4 | 4 | 4 | 87494.2 | 83791 | 95231 | `bash scripts/reproduce_all.sh` |
| no-ipfs | 4 | 4 | 2074.0 | 1907 | 2276 | `bash scripts/baselines/run_no_ipfs.sh` |
| oracle-only | 4 | 4 | 1707.0 | 1682 | 1725 | `bash scripts/baselines/run_oracle_only.sh` |

## Per-run evidence

| Run ID | Variant | Repeat | Status | Duration ms | Manifest |
|---|---|---:|---|---:|---|
| `stage_b_20260627_233849_full-l4_clean_r1` | full-l4 | 1 | PASS | 95231 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_full-l4_clean_r1/manifest.json` |
| `stage_b_20260627_233849_full-l4_clean_r2` | full-l4 | 2 | PASS | 83791 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_full-l4_clean_r2/manifest.json` |
| `stage_b_20260627_233849_full-l4_clean_r3` | full-l4 | 3 | PASS | 84663 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_full-l4_clean_r3/manifest.json` |
| `stage_b_20260627_233849_full-l4_clean_r4` | full-l4 | 4 | PASS | 86292 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_full-l4_clean_r4/manifest.json` |
| `stage_b_20260627_233849_no-ipfs_clean_r1` | no-ipfs | 1 | PASS | 2276 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_no-ipfs_clean_r1/manifest.json` |
| `stage_b_20260627_233849_no-ipfs_clean_r2` | no-ipfs | 2 | PASS | 1907 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_no-ipfs_clean_r2/manifest.json` |
| `stage_b_20260627_233849_no-ipfs_clean_r3` | no-ipfs | 3 | PASS | 2010 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_no-ipfs_clean_r3/manifest.json` |
| `stage_b_20260627_233849_no-ipfs_clean_r4` | no-ipfs | 4 | PASS | 2103 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_no-ipfs_clean_r4/manifest.json` |
| `stage_b_20260627_233849_oracle-only_clean_r1` | oracle-only | 1 | PASS | 1704 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_oracle-only_clean_r1/manifest.json` |
| `stage_b_20260627_233849_oracle-only_clean_r2` | oracle-only | 2 | PASS | 1725 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_oracle-only_clean_r2/manifest.json` |
| `stage_b_20260627_233849_oracle-only_clean_r3` | oracle-only | 3 | PASS | 1717 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_oracle-only_clean_r3/manifest.json` |
| `stage_b_20260627_233849_oracle-only_clean_r4` | oracle-only | 4 | PASS | 1682 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_b_20260627_233849_oracle-only_clean_r4/manifest.json` |

## Claim boundary

This Stage B run is a local n8n-orchestrated repeatability test over the clean profile. It supports reproducible workflow execution and baseline repeatability claims for the tested variants. It should not be described as production O-RAN deployment, packet-capture media KPI measurement, or full public-chain benchmarking.

Raw per-run manifests are stored under `runtime_artifacts/n8n/runs/` and the compact manifest index is stored as `stage_b_12run_manifest_index.jsonl`.
