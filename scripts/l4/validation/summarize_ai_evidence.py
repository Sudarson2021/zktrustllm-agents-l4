#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import pathlib
import statistics
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258/ai_evidence"
OUT.mkdir(parents=True, exist_ok=True)

EF_CANDIDATES = [
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios/records.jsonl",
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios_final_90_v2/records.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl",
]

FF_CANDIDATES = [
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_20260705_192119.jsonl",
]

def read_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows

def get_any(d, keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default

def summarize_rows(rows):
    providers = Counter()
    scenarios = Counter()
    statuses = Counter()
    hashed = 0
    latencies = []

    for r in rows:
        providers[str(get_any(r, ["provider", "model_provider", "vendor"], "unknown"))] += 1
        scenarios[str(get_any(r, ["scenario", "tool_scenario", "case", "task"], "unknown"))] += 1
        statuses[str(get_any(r, ["status", "result_status"], "unknown"))] += 1

        if get_any(r, ["raw_response_sha256", "response_sha256", "raw_sha256"]):
            hashed += 1

        val = get_any(r, ["latency_ms", "duration_ms", "elapsed_ms", "total_latency_ms"])
        try:
            if val is not None:
                latencies.append(float(val))
        except Exception:
            pass

    return {
        "rows": len(rows),
        "hashed_rows": hashed,
        "providers": dict(providers),
        "scenarios": dict(scenarios),
        "statuses": dict(statuses),
        "latency_ms": {
            "count": len(latencies),
            "mean": statistics.mean(latencies) if latencies else None,
            "p50": statistics.median(latencies) if latencies else None,
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None
        }
    }

ef_path = next((p for p in EF_CANDIDATES if p.exists()), None)
ff_path = next((p for p in FF_CANDIDATES if p.exists()), None)

ef_rows = read_jsonl(ef_path) if ef_path else []
ff_rows = read_jsonl(ff_path) if ff_path else []

summary = {
    "claim_boundary": "Summaries are computed only from existing JSONL rows. Missing latency/hash/status fields are not imputed.",
    "stage_ef": {
        "source": str(ef_path) if ef_path else None,
        **summarize_rows(ef_rows)
    },
    "stage_ff": {
        "source": str(ff_path) if ff_path else None,
        **summarize_rows(ff_rows)
    }
}

json_path = OUT / "ai_evidence_summary.json"
json_path.write_text(json.dumps(summary, indent=2) + "\n")

md_lines = [
    "# AI Evidence Summary",
    "",
    "Claim boundary: summaries are computed only from existing JSONL rows. Missing fields are not imputed.",
    "",
    "## Stage E/F",
    "",
    f"- Source: `{summary['stage_ef']['source']}`",
    f"- Rows: {summary['stage_ef']['rows']}",
    f"- Hashed rows: {summary['stage_ef']['hashed_rows']}",
    f"- Providers: `{summary['stage_ef']['providers']}`",
    f"- Scenarios: `{summary['stage_ef']['scenarios']}`",
    f"- Statuses: `{summary['stage_ef']['statuses']}`",
    f"- Latency ms: `{summary['stage_ef']['latency_ms']}`",
    "",
    "## Stage F/F",
    "",
    f"- Source: `{summary['stage_ff']['source']}`",
    f"- Rows: {summary['stage_ff']['rows']}",
    f"- Hashed rows: {summary['stage_ff']['hashed_rows']}",
    f"- Providers: `{summary['stage_ff']['providers']}`",
    f"- Scenarios: `{summary['stage_ff']['scenarios']}`",
    f"- Statuses: `{summary['stage_ff']['statuses']}`",
    f"- Latency ms: `{summary['stage_ff']['latency_ms']}`",
    ""
]

(OUT / "ai_evidence_summary.md").write_text("\n".join(md_lines))
print(json_path)
print(OUT / "ai_evidence_summary.md")
