#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path
from statistics import mean, median, stdev

ROOT = Path(".").resolve()
RUNS = ROOT / "evaluation_runs" / "l4" / "n8n_runs"
OUT = ROOT / "docs" / "l4" / "supervisor_258" / "results"
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
    "post_auto_score_gas",
    "mock_verifier_deploy_gas",
    "reputation_manager_deploy_gas",
    "hardhat_passing_tests",
    "hardhat_failing_tests",
]

BOOL_KEYS = [
    "replay_rejected",
    "zero_anchor_rejected",
    "unauthorized_submitter_rejected",
    "setweights_legacy_error",
    "array_length_error",
    "unauthorized_reverted_observed",
]

SOURCE_KEYS = [
    "prover_time_source",
    "anchor_gas_source",
    "reason_latency_source",
    "rtp_jitter_ms_source",
    "rtp_loss_pct_source",
    "dtls_rtp_jitter_ms_source",
    "dtls_rtp_loss_pct_source",
    "replay_rejected_source",
    "zero_anchor_rejected_source",
    "unauthorized_submitter_source",
]

def timestamp_from_run_id(run_id: str) -> str:
    m = re.search(r"_(\d{8}T\d{6}Z)$", run_id)
    return m.group(1) if m else ""

def safe_float(x):
    if x is None or x == "":
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
        r = json.loads(path.read_text())
        r["_source_path"] = str(path)
        r["_timestamp_key"] = timestamp_from_run_id(r.get("run_id", ""))
        records.append(r)
    except Exception as exc:
        print(f"[warn] failed to read {path}: {exc}")

latest = {}
for r in records:
    key = (r.get("variant"), r.get("profile"), str(r.get("repeat")))
    old = latest.get(key)
    if old is None or r.get("_timestamp_key", "") > old.get("_timestamp_key", ""):
        latest[key] = r

clean = list(latest.values())
clean.sort(key=lambda r: (r.get("variant", ""), r.get("profile", ""), int(r.get("repeat", 0))))

csv_path = OUT / "n8n_all_runs_240runs_duration.csv"
fields = [
    "run_id", "variant", "profile", "repeat", "status",
    "git_commit", "evidence_sha256"
] + NUMERIC_KEYS + BOOL_KEYS + SOURCE_KEYS

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in clean:
        writer.writerow({k: r.get(k) for k in fields})

groups = {}
for r in clean:
    groups.setdefault((r.get("variant", "unknown"), r.get("profile", "unknown")), []).append(r)

md = []
md.append("# Supervisor 258 n8n Evaluation Summary")
md.append("")
md.append("Dataset type: deduplicated clean 240-run duration dataset")
md.append("")
md.append(f"Raw records found before deduplication: {len(records)}")
md.append(f"Clean records after keeping latest variant/profile/repeat: {len(clean)}")
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

summary_path = OUT / "n8n_evaluation_summary_240runs_duration.md"
summary_path.write_text("\n".join(md))

print(f"[ok] raw records: {len(records)}")
print(f"[ok] clean records: {len(clean)}")
print(f"[ok] wrote {csv_path}")
print(f"[ok] wrote {summary_path}")

if len(clean) != 240:
    raise SystemExit(f"[error] expected 240 clean records, got {len(clean)}")
