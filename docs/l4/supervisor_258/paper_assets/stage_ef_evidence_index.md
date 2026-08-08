# Stage E/F n8n Multimodel and Multi-Agent Evidence Index

## Final clean checkpoints

- Terminal final90 evidence tag: `l4-stageef-n8n-multimodel-final90-v1`
- n8n canvas final90 clean tag: `l4-stageef-n8n-canvas-final90-v3`
- Paper-ready assets tag: `l4-stageef-paper-assets-v1`

## Main branch

- Branch: `l4-supervisor258-n8n-multimodel`

## Final n8n canvas execution

- Final n8n canvas output prefix: `stage_ef_three_model_n8n_final90`
- Raw records: 90
- Stage E records: 45
- Stage F records: 45
- Providers: Claude Fable 5, DeepSeek, Mistral
- Raw PASS/PARTIAL/FAIL: 89/1/0
- Valid JSON: 90/90

## Final result files

- `docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.csv`
- `docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl`
- `docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.md`

## Paper-ready assets

- `docs/l4/supervisor_258/paper_assets/stage_ef_grouped_results.csv`
- `docs/l4/supervisor_258/paper_assets/stage_ef_multimodel_multiagent_results_table.tex`
- `docs/l4/supervisor_258/paper_assets/stage_ef_multimodel_multiagent_results_summary.md`
- `docs/l4/supervisor_258/paper_assets/stage_ef_claim_boundary.md`
- `docs/l4/supervisor_258/paper_assets/stage_ef_manuscript_snippet.tex`

## Implementation scripts

- `scripts/n8n/ai_eval/run_stage_ef_multimodel_eval.py`
- `scripts/n8n/ai_eval/local_ai_eval_server.py`
- `scripts/n8n/ai_eval/make_stage_ef_paper_assets.py`

## n8n workflow file

- `config/n8n/stage_ef_multimodel_multiagent_workflow.json`

## Claim boundary

Supported claim:
The Stage E/F workflow evaluates multimodel and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 evidence artifact using n8n.

Unsupported claims:
- Production O-RAN deployment validation
- Packet-capture network-impairment benchmarking
- Public-chain benchmarking
- Full media-plane QoE validation
- 240-run six-variant ablation
