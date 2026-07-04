#!/usr/bin/env python3
import csv
import json
import os
import pathlib
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

REPO = pathlib.Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "docs/l4/supervisor_258/paper_assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HOST = "127.0.0.1"
PORT = int(os.getenv("STAGE_AF_MASTER_SERVER_PORT", "8768"))

STAGE_EF_CANDIDATES = [
    REPO / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.csv",
    REPO / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.csv",
]

STAGE_FF_CSV = REPO / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.csv"

def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))

def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default

def find_stage_ef_csv():
    for p in STAGE_EF_CANDIDATES:
        if p.exists():
            return p
    return None

def summarise_rows(rows):
    if not rows:
        return {
            "rows": 0,
            "pass": 0,
            "partial": 0,
            "fail": 0,
            "valid_json": 0,
            "mean_accuracy_pct": 0.0,
            "mean_latency_ms": 0.0,
            "mean_cost_usd": 0.0,
        }

    status_counts = Counter(r.get("status", "") for r in rows)

    valid_json = 0
    for r in rows:
        v = str(r.get("valid_json_all", r.get("valid_json", ""))).lower()
        if v in {"true", "1", "yes", "pass"}:
            valid_json += 1

    acc_vals = []
    lat_vals = []
    cost_vals = []

    for r in rows:
        if "final_accuracy" in r:
            acc_vals.append(safe_float(r["final_accuracy"]) * 100.0)
        elif "accuracy" in r:
            a = safe_float(r["accuracy"])
            acc_vals.append(a * 100.0 if a <= 1.0 else a)

        for key in ["total_latency_ms", "latency_ms", "execution_time_ms"]:
            if key in r and r[key] != "":
                lat_vals.append(safe_float(r[key]))
                break

        for key in ["total_estimated_cost_usd", "estimated_cost_usd", "cost_usd"]:
            if key in r and r[key] != "":
                cost_vals.append(safe_float(r[key]))
                break

    return {
        "rows": len(rows),
        "pass": status_counts.get("PASS", 0),
        "partial": status_counts.get("PARTIAL", 0),
        "fail": status_counts.get("FAIL", 0),
        "valid_json": valid_json,
        "mean_accuracy_pct": round(statistics.mean(acc_vals), 2) if acc_vals else 0.0,
        "mean_latency_ms": round(statistics.mean(lat_vals), 2) if lat_vals else 0.0,
        "mean_cost_usd": round(statistics.mean(cost_vals), 8) if cost_vals else 0.0,
    }

def group_by_scenario(rows):
    groups = defaultdict(list)
    for r in rows:
        key = (
            r.get("scenario_id")
            or r.get("scenario")
            or r.get("case_id")
            or r.get("case")
            or r.get("stage")
            or "unknown"
        )
        groups[key].append(r)

    out = []
    for key, rs in sorted(groups.items()):
        s = summarise_rows(rs)
        out.append({
            "scenario": key,
            **s,
        })
    return out

def build_master_summary():
    stage_ef_csv = find_stage_ef_csv()
    ef_rows = read_csv(stage_ef_csv) if stage_ef_csv else []
    ff_rows = read_csv(STAGE_FF_CSV)

    stage_b = {"stage": "B", "description": "Local repeatability", "runs": 12}
    stage_c = {"stage": "C", "description": "Local profile-pilot", "runs": 24}
    stage_d = {"stage": "D-real", "description": "Local real-variant matrix", "runs": 120}
    frozen_total = stage_b["runs"] + stage_c["runs"] + stage_d["runs"]

    ef_summary = summarise_rows(ef_rows)
    ff_summary = summarise_rows(ff_rows)

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "claim_boundary": (
            "This master workflow supports local evidence-grounded orchestration, multi-model baseline evaluation, "
            "multi-agent test cases, and four-model inter-agent communication. It does not claim production O-RAN "
            "deployment validation, packet-capture network benchmarking, public-chain benchmarking, full media-plane "
            "QoE validation, or a 240-run six-variant ablation."
        ),
        "stages": {
            "A": {
                "description": "Experiment initialisation, model configuration, frozen context, and claim boundary."
            },
            "B": stage_b,
            "C": stage_c,
            "D": stage_d,
            "frozen_local_evidence_total": frozen_total,
            "E_F": {
                "description": "Three-model single-agent and multi-agent n8n evaluation using Claude, DeepSeek, and Mistral.",
                "csv": str(stage_ef_csv) if stage_ef_csv else "",
                **ef_summary,
            },
            "F_F": {
                "description": "Four-model inter-agent communication: GPT-5.5 Planner -> Claude Critic -> DeepSeek Recovery -> Mistral Arbiter.",
                "csv": str(STAGE_FF_CSV),
                **ff_summary,
            },
        },
        "stage_ef_by_scenario": group_by_scenario(ef_rows),
        "stage_ff_by_scenario": group_by_scenario(ff_rows),
        "supervisor_feedback_coverage": [
            "n8n workflow diagram",
            "workflow logic explanation",
            "role of each component",
            "Claude, DeepSeek, and Mistral scenarios",
            "GPT-5.5, Claude, DeepSeek, and Mistral inter-agent communication",
            "task decomposition",
            "agent collaboration",
            "failure recovery",
            "verification agent",
            "model disagreement resolution",
            "accuracy",
            "execution time",
            "cost",
            "failed runs",
            "consistency",
            "single-agent baseline comparison",
        ],
    }

    md = []
    md.append("# Stage A-F + F/F Master Supervisor Summary")
    md.append("")
    md.append(f"Generated: {payload['generated']}")
    md.append("")
    md.append("## Claim boundary")
    md.append("")
    md.append(payload["claim_boundary"])
    md.append("")
    md.append("## Evidence stages")
    md.append("")
    md.append("| Stage | Description | Runs / Records | PASS/PARTIAL/FAIL | Valid JSON | Mean accuracy % | Mean latency ms | Mean cost USD |")
    md.append("|---|---|---:|---|---:|---:|---:|---:|")
    md.append(f"| A | Experiment initialisation and claim boundary | -- | -- | -- | -- | -- | -- |")
    md.append(f"| B | Local repeatability | {stage_b['runs']} | -- | -- | -- | -- | -- |")
    md.append(f"| C | Local profile-pilot | {stage_c['runs']} | -- | -- | -- | -- | -- |")
    md.append(f"| D-real | Local real-variant matrix | {stage_d['runs']} | -- | -- | -- | -- | -- |")
    md.append(
        f"| E/F | Three-model AI evaluation | {ef_summary['rows']} | "
        f"{ef_summary['pass']}/{ef_summary['partial']}/{ef_summary['fail']} | "
        f"{ef_summary['valid_json']} | {ef_summary['mean_accuracy_pct']} | "
        f"{ef_summary['mean_latency_ms']} | {ef_summary['mean_cost_usd']} |"
    )
    md.append(
        f"| F/F | Four-model inter-agent communication | {ff_summary['rows']} | "
        f"{ff_summary['pass']}/{ff_summary['partial']}/{ff_summary['fail']} | "
        f"{ff_summary['valid_json']} | {ff_summary['mean_accuracy_pct']} | "
        f"{ff_summary['mean_latency_ms']} | {ff_summary['mean_cost_usd']} |"
    )
    md.append("")
    md.append(f"Frozen local evidence total before AI-assisted stages: **{frozen_total} runs**.")
    md.append("")
    md.append("## Stage F/F scenario results")
    md.append("")
    md.append("| Scenario | Runs | PASS/PARTIAL/FAIL | Valid JSON | Mean accuracy % | Mean latency ms | Mean cost USD |")
    md.append("|---|---:|---|---:|---:|---:|---:|")
    for s in payload["stage_ff_by_scenario"]:
        md.append(
            f"| {s['scenario']} | {s['rows']} | {s['pass']}/{s['partial']}/{s['fail']} | "
            f"{s['valid_json']} | {s['mean_accuracy_pct']} | {s['mean_latency_ms']} | {s['mean_cost_usd']} |"
        )
    md.append("")
    md.append("## Supervisor feedback coverage")
    md.append("")
    for item in payload["supervisor_feedback_coverage"]:
        md.append(f"- {item}")

    json_path = OUT_DIR / "stage_af_ff_master_supervisor_summary.json"
    md_path = OUT_DIR / "stage_af_ff_master_supervisor_summary.md"

    json_path.write_text(json.dumps(payload, indent=2))
    md_path.write_text("\n".join(md) + "\n")

    payload["written_files"] = {
        "json": str(json_path),
        "markdown": str(md_path),
    }

    return payload

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            json_response(self, 200, {
                "ok": True,
                "service": "Stage A-F + F/F master evidence aggregator",
                "repo": str(REPO),
                "stage_ef_csv_found": str(find_stage_ef_csv()) if find_stage_ef_csv() else "",
                "stage_ff_csv_found": STAGE_FF_CSV.exists(),
            })
            return
        json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/build_master_summary":
            json_response(self, 404, {"ok": False, "error": "Unknown endpoint"})
            return

        try:
            payload = build_master_summary()
            json_response(self, 200, {"ok": True, **payload})
        except Exception as e:
            json_response(self, 500, {"ok": False, "error": str(e)})

def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Stage A-F + F/F master aggregator running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /build_master_summary")
    server.serve_forever()

if __name__ == "__main__":
    main()
