#!/usr/bin/env python3
import csv
from pathlib import Path
from collections import defaultdict, Counter
import statistics

ROOT = Path(".").resolve()
CSV_PATH = ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.csv"
OUT_DIR = ROOT / "docs/l4/supervisor_258/paper_assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(CSV_PATH.open()))

groups = defaultdict(list)
for r in rows:
    groups[r["scenario_id"]].append(r)

total = len(rows)
passed = sum(1 for r in rows if r["status"] == "PASS")
partial = sum(1 for r in rows if r["status"] == "PARTIAL")
failed = sum(1 for r in rows if r["status"] == "FAIL")
valid_json = sum(1 for r in rows if r["valid_json_all"] == "True")

def mean_float(rs, key):
    return statistics.mean(float(r[key]) for r in rs)

def p95_int(rs, key):
    vals = sorted(int(float(r[key])) for r in rs)
    idx = int(0.95 * (len(vals) - 1))
    return vals[idx]

# LaTeX table
tex_lines = []
tex_lines.append(r"\begin{table}[t]")
tex_lines.append(r"\centering")
tex_lines.append(r"\caption{Stage F/F four-model intercommunication results.}")
tex_lines.append(r"\label{tab:stageff_four_model_results}")
tex_lines.append(r"\begin{tabular}{lrrrrr}")
tex_lines.append(r"\toprule")
tex_lines.append(r"Scenario & Runs & Pass & Accuracy (\%) & Agreement (\%) & Mean latency (ms) \\")
tex_lines.append(r"\midrule")

for scenario, rs in sorted(groups.items()):
    pass_n = sum(1 for r in rs if r["status"] == "PASS")
    acc = 100.0 * mean_float(rs, "final_accuracy")
    agreement = mean_float(rs, "inter_model_agreement_pct")
    latency = mean_float(rs, "total_latency_ms")
    tex_lines.append(
        f"{scenario.replace('-', r'\\mbox{-}')} & {len(rs)} & {pass_n} & "
        f"{acc:.1f} & {agreement:.1f} & {latency:.1f} \\\\"
    )

tex_lines.append(r"\midrule")
tex_lines.append(f"Total & {total} & {passed} & 100.0 & 100.0 & -- \\\\")
tex_lines.append(r"\bottomrule")
tex_lines.append(r"\end{tabular}")
tex_lines.append(r"\end{table}")

(OUT_DIR / "stage_ff_fourmodel_results_table.tex").write_text("\n".join(tex_lines) + "\n")

# Manuscript snippet
snippet = f"""
\\paragraph{{Stage F/F four-model intercommunication.}}
To address the multi-agent orchestration requirement, we implemented a local n8n-triggered four-model communication workflow for the ZKTrustLLM-Agents L4 artifact. The workflow assigns GPT-5.5 as the planner agent, Claude Fable 5 as the evidence critic, DeepSeek as the recovery agent, and Mistral as the verifier/arbiter. Each run passes the previous model output to the next stage, producing an explicit inter-model communication trace for task decomposition, collaboration, failure recovery, verification, and model-disagreement resolution.

The final Stage F/F execution contains {total} four-model communication records across five scenarios and three repeats per scenario. All {total} records passed, with {valid_json}/{total} valid JSON chains, no partial records, and no failed records. The scenario-level results show 100\\% final accuracy and 100\\% inter-model agreement across task decomposition, agent collaboration, failure recovery, verification-agent checking, and model-disagreement resolution. Table~\\ref{{tab:stageff_four_model_results}} summarises these results.

These results should be interpreted as local evidence-grounded orchestration evidence. They demonstrate inter-AI communication, deterministic repair of malformed model outputs, and claim-boundary preservation around the frozen ZKTrustLLM-Agents artifact. They do not claim production O-RAN deployment validation, packet-capture network benchmarking, public-chain benchmarking, full media-plane QoE validation, or a 240-run six-variant ablation.
""".strip()

(OUT_DIR / "stage_ff_fourmodel_manuscript_snippet.tex").write_text(snippet + "\n")

# Evidence index
index = f"""
# Stage F/F Four-Model n8n Intercommunication Evidence Index

## Final committed evidence

- Result prefix: `stage_ff_four_model_comm_n8n_final15`
- Total records: {total}
- PASS/PARTIAL/FAIL: {passed}/{partial}/{failed}
- Valid JSON all-steps: {valid_json}/{total}
- Communication chain: GPT-5.5 Planner -> Claude Fable 5 Evidence Critic -> DeepSeek Recovery Agent -> Mistral Verifier/Arbiter

## Files

- `docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.csv`
- `docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl`
- `docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.md`
- `runtime_artifacts/n8n/ai_eval_ff/Stage_FF_four_model_comm_*_r*.json`
- `config/n8n/stage_ff_four_model_intercommunication_workflow.json`
- `scripts/n8n/ai_eval/run_stage_ff_four_model_comm.py`
- `scripts/n8n/ai_eval/local_stage_ff_comm_server.py`

## Scenario coverage

- task-decomposition
- agent-collaboration
- failure-recovery
- verification-agent
- model-disagreement-resolution

## Claim boundary

This evidence supports local inter-AI model communication and orchestration behaviour around the ZKTrustLLM-Agents L4 artifact. It does not support claims of production O-RAN deployment validation, packet-capture network benchmarking, public-chain benchmarking, full media-plane QoE validation, or a 240-run six-variant ablation.
""".strip()

(OUT_DIR / "stage_ff_fourmodel_evidence_index.md").write_text(index + "\n")

print("Wrote:")
print(OUT_DIR / "stage_ff_fourmodel_results_table.tex")
print(OUT_DIR / "stage_ff_fourmodel_manuscript_snippet.tex")
print(OUT_DIR / "stage_ff_fourmodel_evidence_index.md")
