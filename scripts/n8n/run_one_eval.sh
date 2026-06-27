#!/usr/bin/env bash
set -u

VARIANT="${1:?variant required}"
PROFILE="${2:?profile required}"
REPEAT="${3:?repeat required}"
RUN_ID="${4:?run_id required}"

OUTDIR="artifacts/out/n8n/runs/${RUN_ID}"
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

set +e
eval "$COMMAND_USED" > "$OUTDIR/stdout.log" 2> "$OUTDIR/stderr.log"
EXIT_CODE=$?
set -e

END_NS="$(date +%s%N)"
DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))

if [ "$EXIT_CODE" -ne 0 ] && [ "$STATUS" = "PASS" ]; then
  STATUS="FAIL"
fi

sha256sum "$OUTDIR/stdout.log" "$OUTDIR/stderr.log" > "$OUTDIR/SHA256SUMS.txt" 2>/dev/null || true

python3 - <<PY
import json, pathlib, re

outdir = pathlib.Path("$OUTDIR")
stdout = (outdir / "stdout.log").read_text(errors="ignore") if (outdir / "stdout.log").exists() else ""
stderr = (outdir / "stderr.log").read_text(errors="ignore") if (outdir / "stderr.log").exists() else ""

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
    r"anchor gas\\D+(\\d+)",
    r"gasUsed\\D+(\\d+)",
    r"gas used\\D+(\\d+)"
], stdout + "\\n" + stderr)

manifest = {
    "run_id": "$RUN_ID",
    "variant": "$VARIANT",
    "profile": "$PROFILE",
    "repeat": int("$REPEAT"),
    "git_hash": "$GIT_HASH",
    "start_ts": "$START_TS",
    "duration_ms": $DURATION_MS,
    "status": "$STATUS",
    "exit_code": $EXIT_CODE,
    "command_used": "$COMMAND_USED",
    "anchor_gas_detected": anchor_gas,
    "stdout_path": str(outdir / "stdout.log"),
    "stderr_path": str(outdir / "stderr.log"),
    "sha256_path": str(outdir / "SHA256SUMS.txt")
}

(outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("N8N_JSON=" + json.dumps(manifest))
PY
