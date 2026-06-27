#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(".").resolve()
RUNS = ROOT / "evaluation_runs" / "l4" / "n8n_runs"

GAS_PATTERNS = {
    "post_auto_score_gas": r"postAutoScore\s+.*?([\d,]+)\s+·\s+\d+",
    "mock_verifier_deploy_gas": r"MockVerifier\s+.*?([\d,]+)\s+·\s+",
    "reputation_manager_deploy_gas": r"ReputationManager\s+.*?([\d,]+)\s+·\s+",
}

def to_int(value):
    if value is None:
        return None
    return int(str(value).replace(",", "").strip())

def parse_log_text(text):
    out = {}

    for key, pattern in GAS_PATTERNS.items():
        m = re.search(pattern, text)
        out[key] = to_int(m.group(1)) if m else None

    passing = re.search(r"(\d+)\s+passing", text)
    failing = re.search(r"(\d+)\s+failing", text)

    out["hardhat_passing_tests"] = int(passing.group(1)) if passing else None
    out["hardhat_failing_tests"] = int(failing.group(1)) if failing else None

    out["setweights_legacy_error"] = "setWeights is not a function" in text
    out["array_length_error"] = "array is wrong length" in text
    out["unauthorized_reverted_observed"] = "reverted" in text.lower()

    return out

updated = 0
missing = 0

for kpis_path in sorted(RUNS.glob("*/kpis.json")):
    run_dir = kpis_path.parent
    raw_log = run_dir / "raw.log"
    hardhat_log = run_dir / "hardhat_test.log"

    text = ""
    if raw_log.exists():
        text += raw_log.read_text(errors="ignore") + "\n"
    if hardhat_log.exists():
        text += hardhat_log.read_text(errors="ignore") + "\n"

    if not text.strip():
        missing += 1
        continue

    data = json.loads(kpis_path.read_text())
    parsed = parse_log_text(text)

    data.update(parsed)

    # Map available Hardhat gas to broader paper KPI names where useful.
    if data.get("post_auto_score_gas") is not None:
        data["verifier_gas"] = data.get("post_auto_score_gas")

    kpis_path.write_text(json.dumps(data, indent=2) + "\n")
    updated += 1

print(f"[ok] updated kpis files: {updated}")
print(f"[ok] missing logs: {missing}")
