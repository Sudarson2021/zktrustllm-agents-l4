#!/usr/bin/env python3
import csv
import pathlib
import statistics
from collections import defaultdict, Counter
from datetime import datetime

ROOT = pathlib.Path(".").resolve()
CSV_PATH = ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.csv"
OUT_DIR = ROOT / "docs/l4/supervisor_258/paper_assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUPED_CSV = OUT_DIR / "stage_ef_grouped_results.csv"
TEX_TABLE = OUT_DIR / "stage_ef_multimodel_multiagent_results_table.tex"
MD_SUMMARY = OUT_DIR / "stage_ef_multimodel_multiagent_results_summary.md"
CLAIM_BOUNDARY = OUT_DIR / "stage_ef_claim_boundary.md"

if not CSV_PATH.exists():
    raise SystemExit(f"Missing input CSV: {CSV_PATH}")

with CSV_PATH.open(newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("CSV exists but contains no rows.")

def ffloat(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def fint(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default

def p95(values):
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(0.95 * (len(values) - 1))
    return values[idx]

def model_short(model):
    model = model or ""
    if "claude" in model.lower():
        return "Claude Fable 5"
    if "deepseek" in model.lower():
        return "DeepSeek"
    if "mistral" in model.lower():
        return "Mistral"
    return model

def stage_short(stage):
    if stage == "Stage_E_single_agent":
        return "Stage E"
    if stage == "Stage_F_multi_agent":
        return "Stage F"
    return stage

groups = defaultdict(list)

for r in rows:
    stage = r.get("stage", "")
    provider = r.get("provider", "")
    model = r.get("model_id", "")

    if stage == "Stage_E_single_agent":
        scenario = r.get("scenario_id", "")
    elif stage == "Stage_F_multi_agent":
        # Compact paper table: aggregate all five multi-agent cases per provider.
        scenario = "multi-agent cases"
    else:
        scenario = r.get("scenario_id", "") or r.get("case_id", "")

    groups[(stage, provider, model, scenario)].append(r)

grouped = []
for (stage, provider, model, scenario), rs in sorted(groups.items()):
    statuses = Counter(r.get("status", "FAIL") for r in rs)
    valid_json_pct = 100.0 * sum(str(r.get("valid_json", "")).lower() == "true" for r in rs) / len(rs)
    accuracies = [ffloat(r.get("accuracy")) for r in rs]
    latencies = [fint(r.get("latency_ms")) for r in rs]
    costs = [ffloat(r.get("estimated_cost_usd")) for r in rs]
    hashes = [r.get("output_hash", "") for r in rs if r.get("output_hash", "")]

    consistency = 0.0
    if hashes:
        majority_hash, majority_count = Counter(hashes).most_common(1)[0]
        consistency = 100.0 * majority_count / len(hashes)

    grouped.append({
        "stage": stage,
        "stage_label": stage_short(stage),
        "provider": provider,
        "model_id": model,
        "model_label": model_short(model),
        "scenario_or_case": scenario,
        "runs": len(rs),
        "pass_partial_fail": f"{statuses.get('PASS', 0)}/{statuses.get('PARTIAL', 0)}/{statuses.get('FAIL', 0)}",
        "valid_json_pct": round(valid_json_pct, 1),
        "mean_accuracy_pct": round(100.0 * statistics.mean(accuracies), 1),
        "mean_latency_ms": round(statistics.mean(latencies), 1),
        "p95_latency_ms": round(p95(latencies), 1),
        "mean_cost_run_usd": round(statistics.mean(costs), 8),
        "consistency_pct": round(consistency, 1),
    })

# Write grouped CSV for inspection.
with GROUPED_CSV.open("w", newline="") as f:
    fieldnames = list(grouped[0].keys())
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(grouped)

# LaTeX table.
lines = []
lines.append(r"\begin{table}[t]")
lines.append(r"\centering")
lines.append(r"\caption{Stage E/F multimodel and multi-agent n8n evaluation results. Costs are reported using the configured pricing variables in the experiment environment.}")
lines.append(r"\label{tab:stage-ef-n8n-results}")
lines.append(r"\scriptsize")
lines.append(r"\begin{tabular}{llrrrrrr}")
lines.append(r"\hline")
lines.append(r"Stage/Task & Model & Runs & Pass/Partial/Fail & Valid JSON & Accuracy & Mean Lat. & Consistency \\")
lines.append(r" & & & & (\%) & (\%) & (ms) & (\%) \\")
lines.append(r"\hline")

for r in grouped:
    stage_task = f"{r['stage_label']}: {r['scenario_or_case']}"
    lines.append(
        f"{stage_task} & {r['model_label']} & {r['runs']} & {r['pass_partial_fail']} & "
        f"{r['valid_json_pct']:.1f} & {r['mean_accuracy_pct']:.1f} & "
        f"{r['mean_latency_ms']:.1f} & {r['consistency_pct']:.1f} \\\\"
    )

lines.append(r"\hline")
lines.append(r"\end{tabular}")
lines.append(r"\end{table}")
TEX_TABLE.write_text("\n".join(lines) + "\n")

total_records = len(rows)
stage_e_runs = sum(1 for r in rows if r.get("stage") == "Stage_E_single_agent")
stage_f_runs = sum(1 for r in rows if r.get("stage") == "Stage_F_multi_agent")
pass_total = sum(1 for r in rows if r.get("status") == "PASS")
partial_total = sum(1 for r in rows if r.get("status") == "PARTIAL")
fail_total = sum(1 for r in rows if r.get("status") == "FAIL")
valid_json_total = sum(str(r.get("valid_json", "")).lower() == "true" for r in rows)

md = []
md.append("# Stage E/F paper-ready result summary")
md.append("")
md.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
md.append("")
md.append("## Quantitative summary")
md.append("")
md.append(f"- Total raw model-assisted records: {total_records}")
md.append(f"- Stage E single-agent records: {stage_e_runs}")
md.append(f"- Stage F multi-agent records: {stage_f_runs}")
md.append(f"- PASS/PARTIAL/FAIL raw records: {pass_total}/{partial_total}/{fail_total}")
md.append(f"- Valid JSON raw records: {valid_json_total}/{total_records}")
md.append("")
md.append("## Paper-ready paragraph")
md.append("")
md.append(
    f"We implemented and executed a Stage E/F n8n-based multimodel and multi-agent evaluation workflow around the local "
    f"ZKTrustLLM-Agents L4 artifact. The final n8n canvas execution contains {total_records} model-assisted runs: "
    f"{stage_e_runs} single-agent tool-scenario runs and {stage_f_runs} multi-agent orchestration runs across Claude Fable 5, "
    f"DeepSeek, and Mistral. The workflow records valid JSON rate, task accuracy, execution latency, configured estimated cost, "
    f"failure rate, and output consistency. At the raw-run level, the evaluation produced {pass_total} passing runs, "
    f"{partial_total} partial runs, and {fail_total} failed runs, with valid JSON produced in {valid_json_total}/{total_records} runs. "
    f"These results support a local-artifact claim about evidence-grounded multimodel orchestration, not production O-RAN deployment, "
    f"packet-capture benchmarking, public-chain benchmarking, or full media-plane QoE validation."
)
md.append("")
md.append("## Generated assets")
md.append("")
md.append(f"- Grouped CSV: `{GROUPED_CSV}`")
md.append(f"- LaTeX table: `{TEX_TABLE}`")
md.append(f"- Claim-boundary note: `{CLAIM_BOUNDARY}`")
MD_SUMMARY.write_text("\n".join(md) + "\n")

CLAIM_BOUNDARY.write_text(
"""# Stage E/F claim boundary

Supported claim:
The Stage E/F workflow evaluates multimodel and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 evidence artifact using n8n.

Supported measurements:
- Valid JSON rate
- Task accuracy
- Execution latency
- Configured estimated cost
- Failure rate
- Output consistency
- Single-agent and multi-agent grouped comparisons

Unsupported claims:
- Production O-RAN deployment validation
- Packet-capture network-impairment benchmarking
- Public-chain benchmarking
- Full media-plane QoE validation
- 240-run six-variant ablation
"""
)

print(f"Wrote {GROUPED_CSV}")
print(f"Wrote {TEX_TABLE}")
print(f"Wrote {MD_SUMMARY}")
print(f"Wrote {CLAIM_BOUNDARY}")
