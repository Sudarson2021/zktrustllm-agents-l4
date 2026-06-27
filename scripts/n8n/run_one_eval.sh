#!/usr/bin/env bash
set -uo pipefail

VARIANT="${1:?variant required}"
PROFILE="${2:?profile required}"
REPEAT="${3:?repeat required}"
RUN_ID="${4:?run_id required}"

OUTDIR="runtime_artifacts/n8n/runs/${RUN_ID}"
mkdir -p "$OUTDIR"

GIT_HASH="$(git rev-parse HEAD)"
START_TS="$(date -Iseconds)"
START_NS="$(date +%s%N)"

STATUS="PASS"
COMMAND_USED=""

case "$VARIANT" in
  full-l4)
    COMMAND_USED="bash scripts/reproduce_all.sh"
    ;;
  oracle-only)
    COMMAND_USED="bash scripts/baselines/run_oracle_only.sh"
    ;;
  no-ipfs)
    COMMAND_USED="bash scripts/baselines/run_no_ipfs.sh"
    ;;
  no-zk|rbac-only|no-policy-gate)
    CANDIDATE_SCRIPT="scripts/baselines/run_${VARIANT}.sh"
    if [ -f "$CANDIDATE_SCRIPT" ]; then
      COMMAND_USED="bash $CANDIDATE_SCRIPT"
    else
      STATUS="MISSING_SCRIPT"
      COMMAND_USED="echo Missing baseline script for ${VARIANT}"
    fi
    ;;
  *)
    STATUS="UNKNOWN_VARIANT"
    COMMAND_USED="echo Unknown variant ${VARIANT}"
    ;;
esac

bash -lc "$COMMAND_USED" > "$OUTDIR/stdout.log" 2> "$OUTDIR/stderr.log"
EXIT_CODE=$?

END_NS="$(date +%s%N)"
DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))

if [ "$EXIT_CODE" -ne 0 ] && [ "$STATUS" = "PASS" ]; then
  STATUS="FAIL"
fi

sha256sum "$OUTDIR/stdout.log" "$OUTDIR/stderr.log" > "$OUTDIR/SHA256SUMS.txt" 2>/dev/null || true

export RUN_ID VARIANT PROFILE REPEAT GIT_HASH START_TS DURATION_MS STATUS EXIT_CODE COMMAND_USED OUTDIR

python3 - <<'PY'
import json
import os
import pathlib
import re

outdir = pathlib.Path(os.environ["OUTDIR"])
stdout_path = outdir / "stdout.log"
stderr_path = outdir / "stderr.log"

stdout = stdout_path.read_text(errors="ignore") if stdout_path.exists() else ""
stderr = stderr_path.read_text(errors="ignore") if stderr_path.exists() else ""

def find_int(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except Exception:
                pass
    return None

anchor_gas = find_int([
    r"anchor gas\D+(\d+)",
    r"gasUsed\D+(\d+)",
    r"gas used\D+(\d+)"
], stdout + "\n" + stderr)

manifest = {
    "run_id": os.environ["RUN_ID"],
    "variant": os.environ["VARIANT"],
    "profile": os.environ["PROFILE"],
    "repeat": int(os.environ["REPEAT"]),
    "git_hash": os.environ["GIT_HASH"],
    "start_ts": os.environ["START_TS"],
    "duration_ms": int(os.environ["DURATION_MS"]),
    "status": os.environ["STATUS"],
    "exit_code": int(os.environ["EXIT_CODE"]),
    "command_used": os.environ["COMMAND_USED"],
    "anchor_gas_detected": anchor_gas,
    "stdout_path": str(stdout_path),
    "stderr_path": str(stderr_path),
    "sha256_path": str(outdir / "SHA256SUMS.txt")
}

manifest_path = outdir / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print("N8N_JSON=" + json.dumps(manifest))
PY

if [ ! -f "$OUTDIR/manifest.json" ]; then
  echo "ERROR: manifest was not written for $RUN_ID" >&2
  exit 90
fi

exit "$EXIT_CODE"
