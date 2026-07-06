#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import statistics
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258/zk_timing"
OUT.mkdir(parents=True, exist_ok=True)

rows_path = OUT / "timing_rows.jsonl"
summary_path = OUT / "auth_v2_timing_summary.json"
analysis_json = OUT / "auth_v2_timing_analysis.json"
analysis_md = OUT / "auth_v2_timing_analysis.md"

rows = []
if rows_path.exists():
    for line in rows_path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

durations = [float(r["duration_ms"]) for r in rows if int(r.get("exit_code", 1)) == 0 and r.get("duration_ms") is not None]

verify_values = []
log_errors = []

for r in rows:
    log_path = pathlib.Path(str(r.get("log_path", "")))
    if not log_path.exists():
        continue
    text = log_path.read_text(errors="replace")
    m = re.search(r"verifyTx\s*->\s*(True|False)", text)
    if m:
        verify_values.append(m.group(1) == "True")
    elif int(r.get("exit_code", 1)) != 0:
        log_errors.append(text[:1000])

base_summary = {}
if summary_path.exists():
    try:
        base_summary = json.loads(summary_path.read_text())
    except Exception:
        base_summary = {}

analysis = {
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "timing_status": base_summary.get("status"),
    "runner": base_summary.get("runner"),
    "rows": len(rows),
    "successful_repeats": len(durations),
    "mean_duration_ms": statistics.mean(durations) if durations else None,
    "p50_duration_ms": statistics.median(durations) if durations else None,
    "verify_true_count": sum(1 for v in verify_values if v is True),
    "verify_false_count": sum(1 for v in verify_values if v is False),
    "verify_observed_count": len(verify_values),
    "claim_boundary": "AUTH_V2.2 timing is a local verifier-call timing smoke test. It is proof-validity evidence only if verify_true_count equals successful_repeats and the proof/input artifact is mapped to the manuscript claim.",
    "errors_observed": len(log_errors)
}

analysis_json.write_text(json.dumps(analysis, indent=2) + "\n")

md = [
    "# AUTH_V2.2 Timing Analysis",
    "",
    f"- Timing status: `{analysis['timing_status']}`",
    f"- Successful repeats: `{analysis['successful_repeats']}`",
    f"- Mean duration ms: `{analysis['mean_duration_ms']}`",
    f"- P50 duration ms: `{analysis['p50_duration_ms']}`",
    f"- verifyTx true count: `{analysis['verify_true_count']}`",
    f"- verifyTx false count: `{analysis['verify_false_count']}`",
    "",
    "Claim boundary: this is a local verifier-call timing smoke test. Do not report it as full prover coverage or proof-validity evidence unless every row is mapped to a direct prover/proof log and verifyTx succeeds."
]
analysis_md.write_text("\n".join(md) + "\n")

print(analysis_json)
print(analysis_md)
