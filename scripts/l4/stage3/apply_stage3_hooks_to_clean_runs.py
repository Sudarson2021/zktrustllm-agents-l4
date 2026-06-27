#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(".").resolve()
RUNS = ROOT / "evaluation_runs" / "l4" / "n8n_runs"
HOOK = ROOT / "scripts" / "l4" / "stage3" / "run_stage3_runtime_hooks.sh"

def timestamp_from_run_id(run_id: str) -> str:
    m = re.search(r"_(\d{8}T\d{6}Z)$", run_id)
    return m.group(1) if m else ""

records = []

for kpis_path in sorted(RUNS.glob("*/kpis.json")):
    try:
        data = json.loads(kpis_path.read_text())
        data["_path"] = kpis_path
        data["_timestamp_key"] = timestamp_from_run_id(data.get("run_id", ""))
        records.append(data)
    except Exception as exc:
        print(f"[warn] failed to read {kpis_path}: {exc}")

latest = {}

for data in records:
    key = (data.get("variant"), data.get("profile"), str(data.get("repeat")))
    old = latest.get(key)
    if old is None or data.get("_timestamp_key", "") > old.get("_timestamp_key", ""):
        latest[key] = data

clean = list(latest.values())
clean.sort(key=lambda r: (r.get("variant", ""), r.get("profile", ""), int(r.get("repeat", 0))))

print(f"[stage3] raw records: {len(records)}")
print(f"[stage3] clean records selected: {len(clean)}")

if len(clean) != 240:
    raise SystemExit(f"[error] expected 240 clean records, got {len(clean)}")

for i, data in enumerate(clean, start=1):
    run_dir = data["_path"].parent
    out_log = run_dir / "stage3_runtime_hooks.log"

    variant = data.get("variant")
    profile = data.get("profile")
    repeat = str(data.get("repeat"))

    print(f"[stage3] {i:03d}/240 {variant} {profile} r{repeat}")

    result = subprocess.run(
        [str(HOOK), variant, profile, repeat],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    out_log.write_text(result.stdout)

    if result.returncode != 0:
        print(result.stdout)
        raise SystemExit(f"[error] Stage 3 hook failed for {run_dir}")

print("[stage3] completed direct runtime hooks for clean 240 runs")
