# Stage C: 24-run n8n profile-pilot evidence

Generated: 2026-06-28T00:06:59
Batch ID: `20260627_235121`
Total records: 24
Passed records: 24
Failed records: 0
Git hash: `05aa9266b5131f557b38117228f2aa9d7446a87e`

## Variant/profile summary

| Variant | Profile | Runs | Passed | Mean duration ms | Min | Max | Command |
|---|---|---:|---:|---:|---:|---:|---|
| full-l4 | clean | 2 | 2 | 94622.0 | 88237 | 101007 | `bash scripts/reproduce_all.sh` |
| full-l4 | delay | 2 | 2 | 90321.5 | 89731 | 90912 | `bash scripts/reproduce_all.sh` |
| full-l4 | delay_jitter | 2 | 2 | 93491.5 | 92309 | 94674 | `bash scripts/reproduce_all.sh` |
| full-l4 | delay_jitter_loss | 2 | 2 | 95621.0 | 94659 | 96583 | `bash scripts/reproduce_all.sh` |
| no-ipfs | clean | 2 | 2 | 2109.0 | 2057 | 2161 | `bash scripts/baselines/run_no_ipfs.sh` |
| no-ipfs | delay | 2 | 2 | 1983.5 | 1921 | 2046 | `bash scripts/baselines/run_no_ipfs.sh` |
| no-ipfs | delay_jitter | 2 | 2 | 2010.5 | 1962 | 2059 | `bash scripts/baselines/run_no_ipfs.sh` |
| no-ipfs | delay_jitter_loss | 2 | 2 | 2113.5 | 2048 | 2179 | `bash scripts/baselines/run_no_ipfs.sh` |
| oracle-only | clean | 2 | 2 | 1690.5 | 1676 | 1705 | `bash scripts/baselines/run_oracle_only.sh` |
| oracle-only | delay | 2 | 2 | 1580.0 | 1526 | 1634 | `bash scripts/baselines/run_oracle_only.sh` |
| oracle-only | delay_jitter | 2 | 2 | 1513.5 | 1508 | 1519 | `bash scripts/baselines/run_oracle_only.sh` |
| oracle-only | delay_jitter_loss | 2 | 2 | 1693.0 | 1666 | 1720 | `bash scripts/baselines/run_oracle_only.sh` |

## Per-run evidence

| Run ID | Variant | Profile | Repeat | Status | Duration ms | Manifest |
|---|---|---|---:|---|---:|---|
| `stage_c_20260627_235121_full-l4_clean_r1` | full-l4 | clean | 1 | PASS | 101007 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_clean_r1/manifest.json` |
| `stage_c_20260627_235121_full-l4_clean_r2` | full-l4 | clean | 2 | PASS | 88237 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_clean_r2/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_r1` | full-l4 | delay | 1 | PASS | 89731 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_r1/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_r2` | full-l4 | delay | 2 | PASS | 90912 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_r2/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_jitter_r1` | full-l4 | delay_jitter | 1 | PASS | 92309 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_jitter_r1/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_jitter_r2` | full-l4 | delay_jitter | 2 | PASS | 94674 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_jitter_r2/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_jitter_loss_r1` | full-l4 | delay_jitter_loss | 1 | PASS | 94659 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_jitter_loss_r1/manifest.json` |
| `stage_c_20260627_235121_full-l4_delay_jitter_loss_r2` | full-l4 | delay_jitter_loss | 2 | PASS | 96583 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_full-l4_delay_jitter_loss_r2/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_clean_r1` | no-ipfs | clean | 1 | PASS | 2161 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_clean_r1/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_clean_r2` | no-ipfs | clean | 2 | PASS | 2057 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_clean_r2/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_r1` | no-ipfs | delay | 1 | PASS | 2046 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_r1/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_r2` | no-ipfs | delay | 2 | PASS | 1921 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_r2/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_jitter_r1` | no-ipfs | delay_jitter | 1 | PASS | 1962 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_jitter_r1/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_jitter_r2` | no-ipfs | delay_jitter | 2 | PASS | 2059 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_jitter_r2/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_jitter_loss_r1` | no-ipfs | delay_jitter_loss | 1 | PASS | 2179 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_jitter_loss_r1/manifest.json` |
| `stage_c_20260627_235121_no-ipfs_delay_jitter_loss_r2` | no-ipfs | delay_jitter_loss | 2 | PASS | 2048 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_no-ipfs_delay_jitter_loss_r2/manifest.json` |
| `stage_c_20260627_235121_oracle-only_clean_r1` | oracle-only | clean | 1 | PASS | 1705 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_clean_r1/manifest.json` |
| `stage_c_20260627_235121_oracle-only_clean_r2` | oracle-only | clean | 2 | PASS | 1676 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_clean_r2/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_r1` | oracle-only | delay | 1 | PASS | 1634 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_r1/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_r2` | oracle-only | delay | 2 | PASS | 1526 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_r2/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_jitter_r1` | oracle-only | delay_jitter | 1 | PASS | 1508 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_jitter_r1/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_jitter_r2` | oracle-only | delay_jitter | 2 | PASS | 1519 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_jitter_r2/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_jitter_loss_r1` | oracle-only | delay_jitter_loss | 1 | PASS | 1666 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_jitter_loss_r1/manifest.json` |
| `stage_c_20260627_235121_oracle-only_delay_jitter_loss_r2` | oracle-only | delay_jitter_loss | 2 | PASS | 1720 | `/home/sk02352/zktrustllm-agents-l4/runtime_artifacts/n8n/runs/stage_c_20260627_235121_oracle-only_delay_jitter_loss_r2/manifest.json` |

## Claim boundary

This Stage C run is a local n8n-orchestrated profile-pilot over labelled profiles: clean, delay, delay_jitter, and delay_jitter_loss. It supports workflow repeatability and profile-labelled orchestration evidence. Unless these profiles are later connected to tc/netem, VLC/tshark, or O-RAN telemetry, the results should not be described as measured packet-level network impairment performance.

This evidence should also not be described as production O-RAN deployment, public-chain benchmarking, or real media-plane QoE validation.

Raw per-run manifests are stored under `runtime_artifacts/n8n/runs/`, and the compact manifest index is stored as `stage_c_24run_manifest_index.jsonl`.
