#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258"
VAL = OUT / "validation"
VAL.mkdir(parents=True, exist_ok=True)

checks = []

def add(name, status, evidence, claim_boundary):
    checks.append({
        "name": name,
        "status": status,
        "evidence": evidence,
        "claim_boundary": claim_boundary
    })

def exists_rel(path: str) -> bool:
    return (ROOT / path).exists()

def read_json(path: pathlib.Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

add(
    "artifact_mapping",
    "PASS" if exists_rel("ARTIFACTS.md") else "FAIL",
    "ARTIFACTS.md",
    "Paper claims must map to scripts and generated files."
)

add(
    "journal_readme",
    "PASS" if exists_rel("README.md") else "FAIL",
    "README.md",
    "README should describe the L4 journal artifact and claim boundary."
)

add(
    "pricing_config",
    "PASS" if exists_rel("config/n8n/model_pricing_2026_07.json") else "MISSING",
    "config/n8n/model_pricing_2026_07.json",
    "Pricing is time-sensitive and must be checked again before final submission."
)

media_summary_path = OUT / "media_capture/packet_telemetry_summary.json"
media_summary = read_json(media_summary_path)

if media_summary and media_summary.get("status") == "CAPTURED":
    add(
        "direct_telemetry_packet_capture",
        "PASS",
        str(media_summary_path),
        media_summary.get("claim_boundary")
    )
elif media_summary:
    add(
        "direct_telemetry_packet_capture",
        "BOUNDED",
        str(media_summary_path),
        media_summary.get("claim_boundary")
    )
else:
    add(
        "direct_telemetry_packet_capture",
        "MISSING",
        str(media_summary_path),
        "No packet-capture claim should be made unless this file exists and reports CAPTURED."
    )

zk_summary_path = OUT / "zk_timing/auth_v2_timing_summary.json"
zk_summary = read_json(zk_summary_path)

if zk_summary and zk_summary.get("status") == "DIRECT_AUTH_V2_TIMING_COLLECTED":
    add(
        "auth_v2_timing",
        "BOUNDED",
        str(zk_summary_path),
        zk_summary.get("claim_boundary")
    )
elif zk_summary:
    add(
        "auth_v2_timing",
        "BOUNDED",
        str(zk_summary_path),
        zk_summary.get("claim_boundary")
    )
else:
    add(
        "auth_v2_timing",
        "MISSING",
        str(zk_summary_path),
        "Report AUTH_V2.x timing as partial or missing unless direct timing exists."
    )

ai_record_candidates = [
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios/records.jsonl",
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios_final_90_v2/records.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl",
]

ai_records_path = next((x for x in ai_record_candidates if x.exists()), ai_record_candidates[0])

if ai_records_path.exists():
    rows = []
    for line in ai_records_path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    live = [
        r for r in rows
        if str(r.get("status", "")).startswith("COMPLETED")
        and r.get("raw_response_sha256")
    ]

    add(
        "stage_ef_live_ai_records",
        "PASS" if live else "BOUNDED",
        str(ai_records_path),
        f"Only {len(live)} live hashed provider rows are reportable as live AI evidence."
    )
else:
    add(
        "stage_ef_live_ai_records",
        "MISSING",
        str(ai_records_path),
        "Do not report live Stage E/F model results unless hashed live records exist."
    )

ff_dir = ROOT / "runtime_artifacts/n8n/ai_eval_ff"
ff_files = sorted(ff_dir.glob("Stage_FF_four_model_comm_*.json")) if ff_dir.exists() else []

add(
    "stage_ff_multi_agent_records",
    "PASS" if ff_files else "MISSING",
    str(ff_dir),
    f"Found {len(ff_files)} Stage F/F four-model JSON records. Report only records with raw evidence and clear scenario definitions."
)

core_summary = ROOT / "artifacts/out/summary.txt"

add(
    "core_reproduce_summary",
    "PASS" if core_summary.exists() else "MISSING",
    str(core_summary),
    "Use only as core local reproduction evidence; verify record counts before claiming 240 rows."
)

overall = "READY_FOR_SUPERVISOR_UPDATE"
if any(c["status"] == "FAIL" for c in checks):
    overall = "BLOCKED"
elif any(c["status"] == "MISSING" for c in checks):
    overall = "NEEDS_MORE_EVIDENCE_FOR_JOURNAL"
elif any(c["status"] == "BOUNDED" for c in checks):
    overall = "READY_WITH_BOUNDARY_LIMITATIONS"

report = {
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "overall": overall,
    "checks": checks,
    "strict_publication_note": "For journal submission, PASS is preferred. BOUNDED items must be written as limitations, not completed claims."
}

json_path = VAL / "claim_validation_report.json"
json_path.write_text(json.dumps(report, indent=2) + "\n")

lines = [
    "# Paper 258 Claim Validation Report",
    "",
    f"Generated: {report['generated_at_utc']}",
    "",
    f"Overall: **{report['overall']}**",
    "",
    "| Check | Status | Evidence | Claim boundary |",
    "|---|---|---|---|"
]

for c in checks:
    boundary = str(c["claim_boundary"]).replace("\n", " ")
    lines.append(f"| {c['name']} | {c['status']} | `{c['evidence']}` | {boundary} |")

lines.append("")
lines.append("Publication note: BOUNDED items must be reported as limitations or partial evidence, not completed claims.")

md_path = VAL / "claim_validation_report.md"
md_path.write_text("\n".join(lines) + "\n")

print(md_path)
