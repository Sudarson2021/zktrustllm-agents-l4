#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import time
from collections import Counter

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

def read_jsonl(path: pathlib.Path):
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

def has_raw_hash(row: dict) -> bool:
    return bool(
        row.get("raw_response_sha256")
        or row.get("response_sha256")
        or row.get("raw_sha256")
        or row.get("provider_response_sha256")
    )

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
zk_analysis_path = OUT / "zk_timing/auth_v2_timing_analysis.json"
zk_analysis = read_json(zk_analysis_path)

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

if zk_analysis:
    true_count = int(zk_analysis.get("verify_true_count") or 0)
    false_count = int(zk_analysis.get("verify_false_count") or 0)
    ok_count = int(zk_analysis.get("successful_repeats") or 0)

    if ok_count > 0 and false_count == 0 and true_count == ok_count:
        status = "BOUNDED"
        boundary = "Verifier call succeeded and returned true for all observed local repeats, but this remains local timing evidence unless mapped to all Full-L4 rows."
    elif ok_count > 0 and false_count > 0:
        status = "BOUNDED"
        boundary = "Verifier call completed but returned false for at least one repeat. Report as verifier-call timing only, not proof-validity evidence."
    else:
        status = "MISSING"
        boundary = "No successful AUTH_V2.2 verifier-call result was observed."

    add("auth_v2_semantic_result", status, str(zk_analysis_path), boundary)
else:
    add("auth_v2_semantic_result", "MISSING", str(zk_analysis_path), "AUTH_V2.2 timing analysis has not been generated.")

ai_record_candidates = [
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios/records.jsonl",
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios_final_90_v2/records.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl",
]

ai_records_path = next((x for x in ai_record_candidates if x.exists()), ai_record_candidates[0])
ef_rows = read_jsonl(ai_records_path)

if ef_rows:
    status_counts = Counter(str(r.get("status", "unknown")) for r in ef_rows)
    live_hashed = [
        r for r in ef_rows
        if str(r.get("status", "")).startswith("COMPLETED") and has_raw_hash(r)
    ]
    fully_completed = [r for r in ef_rows if str(r.get("status", "")) == "COMPLETED"]
    validation_fail = [r for r in ef_rows if "VALIDATION_FAIL" in str(r.get("status", ""))]

    add(
        "stage_ef_live_hashed_provider_records",
        "PASS" if len(live_hashed) >= 90 else "BOUNDED",
        str(ai_records_path),
        f"{len(live_hashed)} live hashed provider rows found from {len(ef_rows)} Stage E/F rows. Status counts: {dict(status_counts)}."
    )

    add(
        "stage_ef_validator_compliance",
        "PASS" if len(validation_fail) == 0 and len(fully_completed) == len(ef_rows) else "BOUNDED",
        str(ai_records_path),
        f"{len(fully_completed)} fully completed rows and {len(validation_fail)} validation-fail rows. Report validator compliance separately from live-provider coverage."
    )
else:
    add(
        "stage_ef_live_hashed_provider_records",
        "MISSING",
        str(ai_records_path),
        "Do not report live Stage E/F model results unless hashed live records exist."
    )
    add(
        "stage_ef_validator_compliance",
        "MISSING",
        str(ai_records_path),
        "No Stage E/F rows available for validator-compliance assessment."
    )

ff_candidates = [
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_20260705_192119.jsonl",
]

ff_path = next((x for x in ff_candidates if x.exists()), None)
ff_rows = read_jsonl(ff_path) if ff_path else []

ff_dir = ROOT / "runtime_artifacts/n8n/ai_eval_ff"
ff_files = sorted(ff_dir.glob("Stage_FF_four_model_comm_*.json")) if ff_dir.exists() else []

if ff_rows:
    hashed = [r for r in ff_rows if has_raw_hash(r)]
    status_counts = Counter(str(r.get("status", "unknown")) for r in ff_rows)
    add(
        "stage_ff_multi_agent_records",
        "PASS" if len(hashed) == len(ff_rows) and len(ff_rows) >= 15 else "BOUNDED",
        str(ff_path),
        f"{len(ff_rows)} Stage F/F rows found; {len(hashed)} rows contain raw/provider response hashes. Status counts: {dict(status_counts)}."
    )
elif ff_files:
    add(
        "stage_ff_multi_agent_records",
        "BOUNDED",
        str(ff_dir),
        f"Found {len(ff_files)} Stage F/F JSON files but no final JSONL rows with raw/provider hashes. Use evidence_manifest file hashes."
    )
else:
    add(
        "stage_ff_multi_agent_records",
        "MISSING",
        str(ff_dir),
        "No Stage F/F records found."
    )

core_summary = ROOT / "artifacts/out/summary.txt"

add(
    "core_reproduce_summary",
    "PASS" if core_summary.exists() else "MISSING",
    str(core_summary),
    "Use only as core local reproduction evidence; verify record counts before claiming 240 rows."
)

manifest_path = OUT / "evidence_manifest.json"
add(
    "evidence_manifest",
    "PASS" if manifest_path.exists() else "MISSING",
    str(manifest_path),
    "Evidence manifest should hash validation, packet, AUTH, and AI evidence outputs."
)

overall = "READY_FOR_JOURNAL_ARTIFACT_REVIEW"
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
    "strict_publication_note": "For journal submission, PASS is preferred. BOUNDED items must be written as limitations, scoped evidence, or partial evidence, not completed claims."
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
lines.append("Publication note: BOUNDED items must be reported as limitations, scoped evidence, or partial evidence, not completed claims.")

md_path = VAL / "claim_validation_report.md"
md_path.write_text("\n".join(lines) + "\n")

print(md_path)
