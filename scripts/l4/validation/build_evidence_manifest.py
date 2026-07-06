#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/out/paper_258"
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    OUT / "validation/claim_validation_report.json",
    OUT / "validation/claim_validation_report.md",
    OUT / "media_capture/packet_telemetry_summary.json",
    OUT / "zk_timing/auth_v2_timing_summary.json",
    OUT / "ai_evidence/ai_evidence_summary.md",
    OUT / "ai_evidence/stage_ff_row_hash_manifest.md",
    OUT / "ai_evidence/stage_ff_row_hash_manifest.json",
    OUT / "ai_evidence/stage_ef_failure_analysis.md",
    OUT / "ai_evidence/stage_ef_failure_analysis.json",
    OUT / "ai_evidence/ai_evidence_summary.json",
    OUT / "zk_timing/auth_v2_timing_analysis.md",
    OUT / "zk_timing/auth_v2_timing_analysis.json",
    ROOT / "runtime_artifacts/n8n/model_tool_scenarios/records.jsonl",
    ROOT / "runtime_artifacts/n8n/ai_eval_ff",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl",
    ROOT / "docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl",
]

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(cmd):
    try:
        return subprocess.check_output(["git", *cmd], cwd=ROOT, text=True).strip()
    except Exception:
        return None

files = []
for target in TARGETS:
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        files.extend(sorted(p for p in target.rglob("*") if p.is_file()))

seen = set()
entries = []
for path in files:
    if path in seen:
        continue
    seen.add(path)
    rel = path.relative_to(ROOT)
    entries.append({
        "path": str(rel),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path)
    })

manifest = {
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "git_commit": git(["rev-parse", "HEAD"]),
    "git_branch": git(["branch", "--show-current"]),
    "git_status_short": git(["status", "--short"]),
    "claim_boundary": "This manifest records hashes of local evidence files. It does not imply that generated runtime artifacts should all be committed to Git.",
    "files": entries
}

out_path = OUT / "evidence_manifest.json"
out_path.write_text(json.dumps(manifest, indent=2) + "\n")
print(out_path)
print(f"hashed_files={len(entries)}")
