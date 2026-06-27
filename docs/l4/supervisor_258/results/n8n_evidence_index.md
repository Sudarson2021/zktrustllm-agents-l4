# ZKTrustLLM-Agents L4 n8n Evidence Index

This file indexes the frozen n8n-based evaluation evidence for the L4 ZKTrustLLM-Agents journal artifact.

## Frozen checkpoints

| Stage | Tag | Commit | Evidence scope |
|---|---|---|---|
| Integration baseline | `l4-supervisor258-authv22-n8n-merged-v1` | `30917bc846df503b690a7d0a6846f96a33ceb201` | Supervisor-258 integration, AuthV2.2 testnet/frozen-proof evidence, n8n runner baseline |
| Stage B | `l4-stageb-n8n-repeatability-v1` | `05aa9266b5131f557b38117228f2aa9d7446a87e` | 12-run clean-profile repeatability: 3 variants × 4 repeats |
| Stage C | `l4-stagec-n8n-profile-pilot-v1` | `a3fbc44faf097f4d7dbc3551941c0628cf9cfeee` | 24-run profile-pilot: 3 variants × 4 labelled profiles × 2 repeats |

## Stage B evidence files

- `docs/l4/supervisor_258/results/stage_b_12run_repeatability.md`
- `docs/l4/supervisor_258/results/stage_b_12run_repeatability.csv`
- `docs/l4/supervisor_258/results/stage_b_12run_manifest_index.jsonl`
- Raw manifests: `runtime_artifacts/n8n/runs/stage_b_20260627_233849_*/manifest.json`

## Stage C evidence files

- `docs/l4/supervisor_258/results/stage_c_24run_profile_pilot.md`
- `docs/l4/supervisor_258/results/stage_c_24run_profile_pilot.csv`
- `docs/l4/supervisor_258/results/stage_c_24run_manifest_index.jsonl`
- Raw manifests: `runtime_artifacts/n8n/runs/stage_c_20260627_235121_*/manifest.json`

## Claim boundary

Stage B supports local n8n-orchestrated repeatability evidence for the clean profile.

Stage C supports local n8n-orchestrated profile-labelled workflow evidence across clean, delay, delay_jitter, and delay_jitter_loss labels.

These stages should not be described as production O-RAN deployment, packet-capture media-plane measurement, real network impairment benchmarking, public-chain benchmarking, or full QoE validation unless later experiments explicitly add those measurement sources.
