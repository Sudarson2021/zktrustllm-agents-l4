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

## Supervisor 258 n8n multi-model tool scenarios

Purpose:
- Expand the experimental section with measurable n8n test scenarios using Claude, DeepSeek, and Mistral.
- Measure bounded tool-scenario behaviour without fabricating missing values or expanding the trust boundary.

Primary live runner:
- `scripts/l4/n8n/run_multi_model_tool_scenarios.py`

Table builder:
- `scripts/l4/metrics/build_n8n_model_tool_tables.py`

n8n workflow import:
- `workflows/n8n/zktrustllm_l4_multimodel_tool_scenarios.json`

Methodology note:
- `docs/l4/supervisor_258/N8N_MULTI_MODEL_TOOL_SCENARIOS.md`

Live output directory:
- `runtime_artifacts/n8n/model_tool_scenarios/`

Paper table:
- `paper/l4_conference/tables/table_multimodel_tool_scenarios.tex`

Claim boundary:
- Only rows backed by live raw provider responses and SHA256 hashes are paper evidence.
- `SKIPPED_NO_API_KEY` and `offline-rule` rows are not reported as Claude, DeepSeek, or Mistral results.
