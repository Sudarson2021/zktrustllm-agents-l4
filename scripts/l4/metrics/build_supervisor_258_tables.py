#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from statistics import mean, median, stdev

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "artifacts" / "l4" / "n8n_runs"
OUT = ROOT / "artifacts" / "l4" / "supervisor_258"
OUT.mkdir(parents=True, exist_ok=True)

NUMERIC_KEYS = [
    "duration_ms",
    "reason_latency_ms",
    "a2a_reference_bytes",
    "prover_time_ms",
    "verifier_gas",
    "anchor_gas",
    "rtp_jitter_ms",
    "rtp_loss_pct",
    "dtls_rtp_jitter_ms",
    "dtls_rtp_loss_pct",
]

BOOL_KEYS = [
    "replay_rejected",
    "zero_anchor_rejected",
    "unauthorized_submitter_rejected",
]

def safe_float(x):
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None

def p95(values):
    values = sorted(values)
    if not values:
        return None
    return values[int(round(0.95 * (len(values) - 1)))]

records = []
for path in sorted(RUNS.glob("*/kpis.json")):
    try:
        records.append(json.loads(path.read_text()))
    except Exception as exc:
        print(f"[warn] failed to read {path}: {exc}")

csv_path = OUT / "n8n_all_runs.csv"
fields = [
    "run_id", "variant", "profile", "repeat", "status",
    "git_commit", "evidence_sha256"
] + NUMERIC_KEYS + BOOL_KEYS

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in records:
        writer.writerow({k: r.get(k) for k in fields})

groups = {}
for r in records:
    groups.setdefault((r.get("variant", "unknown"), r.get("profile", "unknown")), []).append(r)

md = []
md.append("# Supervisor 258 n8n Evaluation Summary")
md.append("")
md.append(f"Total records: {len(records)}")
md.append("")
md.append("## Variant/Profile Summary")
md.append("")
md.append("| Variant | Profile | Runs | Pass | Fail |")
md.append("|---|---|---:|---:|---:|")

for (variant, profile), rows in sorted(groups.items()):
    pass_count = sum(1 for r in rows if r.get("status") == "PASS")
    fail_count = len(rows) - pass_count
    md.append(f"| {variant} | {profile} | {len(rows)} | {pass_count} | {fail_count} |")

md.append("")
md.append("## Numeric KPI Summary")
md.append("")
md.append("| Variant | Profile | KPI | n | mean | median | std | p95 |")
md.append("|---|---|---|---:|---:|---:|---:|---:|")

for (variant, profile), rows in sorted(groups.items()):
    for key in NUMERIC_KEYS:
        vals = [safe_float(r.get(key)) for r in rows]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        std_value = stdev(vals) if len(vals) > 1 else 0.0
        md.append(
            f"| {variant} | {profile} | {key} | {len(vals)} | "
            f"{mean(vals):.4f} | {median(vals):.4f} | {std_value:.4f} | {p95(vals):.4f} |"
        )

summary_path = OUT / "n8n_evaluation_summary.md"
summary_path.write_text("\n".join(md))

print(f"[ok] wrote {csv_path}")
print(f"[ok] wrote {summary_path}")
