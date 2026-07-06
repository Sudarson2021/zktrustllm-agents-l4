#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258/ai_evidence"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_20260705_192119.jsonl",
]

source = next((p for p in CANDIDATES if p.exists()), None)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get_nested(d, path):
    cur = d
    for part in path:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur

def first_nonempty(*vals):
    for v in vals:
        if v is not None and str(v).strip() and str(v) != "None":
            return v
    return None

def infer_from_paths(obj):
    text = json.dumps(obj, sort_keys=True)
    scenarios = [
        "agent-collaboration",
        "failure-recovery",
        "model-disagreement-resolution",
        "task-decomposition",
        "verification-agent",
    ]
    providers = ["claude", "deepseek", "mistral", "openai", "anthropic"]

    scenario = next((s for s in scenarios if s in text), None)
    provider = next((p for p in providers if p in text.lower()), None)
    return provider, scenario

rows = []
if source:
    for idx, line in enumerate(source.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            obj = {"_parse_error": True, "_raw_line": line}

        inferred_provider, inferred_scenario = infer_from_paths(obj)

        scenario = first_nonempty(
            obj.get("scenario"),
            obj.get("tool_scenario"),
            obj.get("communication_scenario"),
            obj.get("case"),
            obj.get("task"),
            obj.get("scenario_name"),
            get_nested(obj, ["input", "scenario"]),
            get_nested(obj, ["metrics", "scenario"]),
            inferred_scenario,
        )

        provider = first_nonempty(
            obj.get("provider"),
            obj.get("model_provider"),
            obj.get("vendor"),
            obj.get("model"),
            obj.get("judge_model"),
            get_nested(obj, ["input", "provider"]),
            get_nested(obj, ["metrics", "provider"]),
            inferred_provider,
        )

        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
        rows.append({
            "row_index": idx,
            "row_sha256": sha256_bytes(canonical),
            "status": obj.get("status"),
            "scenario": scenario,
            "provider": provider,
            "has_raw_provider_hash": bool(
                obj.get("raw_response_sha256")
                or obj.get("response_sha256")
                or obj.get("raw_sha256")
                or obj.get("provider_response_sha256")
            ),
            "top_level_keys": sorted(obj.keys()),
        })

manifest = {
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source": str(source) if source else None,
    "source_sha256": sha256_bytes(source.read_bytes()) if source else None,
    "rows": rows,
    "row_count": len(rows),
    "rows_with_raw_provider_hash": sum(1 for r in rows if r["has_raw_provider_hash"]),
    "rows_with_inferred_scenario": sum(1 for r in rows if r["scenario"]),
    "rows_with_inferred_provider": sum(1 for r in rows if r["provider"]),
    "claim_boundary": "These are row/file hashes for Stage F/F evidence integrity. They are not raw provider-response hashes unless has_raw_provider_hash is true."
}

json_path = OUT / "stage_ff_row_hash_manifest.json"
json_path.write_text(json.dumps(manifest, indent=2) + "\n")

md = [
    "# Stage F/F Row Hash Manifest",
    "",
    f"- Source: `{manifest['source']}`",
    f"- Source SHA-256: `{manifest['source_sha256']}`",
    f"- Row count: `{manifest['row_count']}`",
    f"- Rows with raw provider hash: `{manifest['rows_with_raw_provider_hash']}`",
    f"- Rows with inferred scenario: `{manifest['rows_with_inferred_scenario']}`",
    f"- Rows with inferred provider/model: `{manifest['rows_with_inferred_provider']}`",
    "",
    "Claim boundary: these are row/file hashes for evidence integrity. They are not raw provider-response hashes unless explicitly present in the row.",
    "",
    "| Row | Status | Scenario | Provider/model | Row SHA-256 | Raw provider hash present |",
    "|---:|---|---|---|---|---|"
]

for r in rows:
    md.append(
        f"| {r['row_index']} | {r['status']} | {r['scenario']} | {r['provider']} | `{r['row_sha256']}` | {r['has_raw_provider_hash']} |"
    )

md_path = OUT / "stage_ff_row_hash_manifest.md"
md_path.write_text("\n".join(md) + "\n")

print(json_path)
print(md_path)
