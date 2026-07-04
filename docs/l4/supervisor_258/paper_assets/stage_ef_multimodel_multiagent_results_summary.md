# Stage E/F paper-ready result summary

Generated: 2026-07-04T16:30:38

## Quantitative summary

- Total raw model-assisted records: 90
- Stage E single-agent records: 45
- Stage F multi-agent records: 45
- PASS/PARTIAL/FAIL raw records: 89/1/0
- Valid JSON raw records: 90/90

## Paper-ready paragraph

We implemented and executed a Stage E/F n8n-based multimodel and multi-agent evaluation workflow around the local ZKTrustLLM-Agents L4 artifact. The final n8n canvas execution contains 90 model-assisted runs: 45 single-agent tool-scenario runs and 45 multi-agent orchestration runs across Claude Fable 5, DeepSeek, and Mistral. The workflow records valid JSON rate, task accuracy, execution latency, configured estimated cost, failure rate, and output consistency. At the raw-run level, the evaluation produced 89 passing runs, 1 partial runs, and 0 failed runs, with valid JSON produced in 90/90 runs. These results support a local-artifact claim about evidence-grounded multimodel orchestration, not production O-RAN deployment, packet-capture benchmarking, public-chain benchmarking, or full media-plane QoE validation.

## Generated assets

- Grouped CSV: `/home/sk02352/zktrustllm-agents-l4/docs/l4/supervisor_258/paper_assets/stage_ef_grouped_results.csv`
- LaTeX table: `/home/sk02352/zktrustllm-agents-l4/docs/l4/supervisor_258/paper_assets/stage_ef_multimodel_multiagent_results_table.tex`
- Claim-boundary note: `/home/sk02352/zktrustllm-agents-l4/docs/l4/supervisor_258/paper_assets/stage_ef_claim_boundary.md`
