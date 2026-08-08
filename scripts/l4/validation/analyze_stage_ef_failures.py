#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258/ai_evidence"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios/records.jsonl",
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios_final_90_v2/records.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl",
]

path = next((p for p in CANDIDATES if p.exists()), None)

rows = []
if path:
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

def get_any(d, keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default

def is_false(v):
    return v is False or str(v).lower() == "false" or v == 0

def derive_reasons(r):
    reasons = []

    checks = [
        "validator_pass",
        "schema_ok",
        "json_parse_ok",
        "arrays_ok",
        "claim_boundary_ok_matches_expected",
        "evidence_class_matches_expected",
        "overclaim_detection_ok",
        "action_class_valid",
    ]

    for key in checks:
        if key in r and is_false(r.get(key)):
            reasons.append(f"{key}=false")

    missing = r.get("missing_schema_keys")
    if isinstance(missing, list) and missing:
        reasons.append("missing_schema_keys=" + ",".join(str(x) for x in missing))
    elif isinstance(missing, str) and missing.strip():
        reasons.append("missing_schema_keys=" + missing)

    try:
        ladder = int(r.get("action_ladder_violation_count", 0) or 0)
        if ladder > 0:
            reasons.append(f"action_ladder_violation_count={ladder}")
    except Exception:
        pass

    err = r.get("error")
    if err:
        reasons.append(f"error={err}")

    return reasons or ["NO_DERIVED_REASON_BUT_STATUS_FAIL"]

status_counts = Counter()
provider_counts = Counter()
scenario_counts = Counter()
reason_counts = Counter()
examples = []

for r in rows:
    status = str(get_any(r, ["status", "result_status"], "unknown"))
    provider = str(get_any(r, ["provider", "model_provider", "vendor"], "unknown"))
    scenario = str(get_any(r, ["tool_scenario", "scenario", "case", "task"], "unknown"))

    status_counts[status] += 1
    provider_counts[provider] += 1
    scenario_counts[scenario] += 1

    if "FAIL" in status or is_false(r.get("validator_pass")):
        reasons = derive_reasons(r)
        for reason in reasons:
            reason_counts[reason] += 1

        if len(examples) < 12:
            examples.append({
                "provider": provider,
                "scenario": scenario,
                "status": status,
                "reason_sample": reasons,
                "validator_fields": {
                    "validator_pass": r.get("validator_pass"),
                    "schema_ok": r.get("schema_ok"),
                    "json_parse_ok": r.get("json_parse_ok"),
                    "arrays_ok": r.get("arrays_ok"),
                    "claim_boundary_ok_matches_expected": r.get("claim_boundary_ok_matches_expected"),
                    "evidence_class_matches_expected": r.get("evidence_class_matches_expected"),
                    "overclaim_detection_ok": r.get("overclaim_detection_ok"),
                    "action_class_valid": r.get("action_class_valid"),
                    "action_ladder_violation_count": r.get("action_ladder_violation_count"),
                    "missing_schema_keys": r.get("missing_schema_keys"),
                    "error": r.get("error"),
                }
            })

summary = {
    "source": str(path) if path else None,
    "rows": len(rows),
    "status_counts": dict(status_counts),
    "provider_counts": dict(provider_counts),
    "scenario_counts": dict(scenario_counts),
    "derived_failure_reason_counts": dict(reason_counts),
    "failure_examples": examples,
    "claim_boundary": "This diagnoses Stage E/F validator failures only. It does not reclassify failed rows as successful."
}

json_path = OUT / "stage_ef_failure_analysis.json"
json_path.write_text(json.dumps(summary, indent=2) + "\n")

md = [
    "# Stage E/F Validation-Failure Analysis",
    "",
    f"- Source: `{summary['source']}`",
    f"- Rows: `{summary['rows']}`",
    f"- Status counts: `{summary['status_counts']}`",
    f"- Provider counts: `{summary['provider_counts']}`",
    f"- Scenario counts: `{summary['scenario_counts']}`",
    "",
    "## Derived failure reasons",
    "",
]

for reason, count in reason_counts.most_common(40):
    md.append(f"- `{count}` × {reason}")

md += ["", "## Failure examples", ""]

for ex in examples:
    md.append(f"- Provider `{ex['provider']}`, scenario `{ex['scenario']}`, status `{ex['status']}`")
    md.append(f"  - Reason sample: `{ex['reason_sample']}`")
    md.append(f"  - Validator fields: `{ex['validator_fields']}`")

md.append("")
md.append("Claim boundary: this analysis diagnoses failed rows only. It does not convert validation failures into successes.")

md_path = OUT / "stage_ef_failure_analysis.md"
md_path.write_text("\n".join(md) + "\n")

print(json_path)
print(md_path)
