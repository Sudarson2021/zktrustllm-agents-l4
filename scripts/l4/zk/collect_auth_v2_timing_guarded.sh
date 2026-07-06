#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT="$ROOT/artifacts/out/paper_258/zk_timing"

mkdir -p "$OUT"

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv-paper258/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

SUMMARY="$OUT/auth_v2_timing_summary.json"
REPEATS="${REPEATS:-3}"

candidates=(
  "scripts/l4/check_auth_v2_2_groth16_verifier.py"
  "scripts/l4/check_auth_v2_2_wrapper.py"
  "scripts/l4/build_auth_v2_2_proof_payload.py"
  "scripts/l4/check_auth_v2_1_groth16_verifier.py"
  "scripts/l4/check_auth_v2_groth16_verifier.py"
)

found=""

for f in "${candidates[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    found="$f"
    break
  fi
done

if [ -z "$found" ]; then
  python3 - <<PY
import json, pathlib, time
path = pathlib.Path("$SUMMARY")
path.write_text(json.dumps({
  "status": "NO_AUTH_V2_RUNNER_FOUND",
  "claim_boundary": "Do not claim complete AUTH_V2.x prover timing. Report as missing or partial future work.",
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}, indent=2) + "\n")
PY
  cat "$SUMMARY"
  exit 0
fi

echo "[RUN] timing candidate: $found"

: > "$OUT/timing_rows.jsonl"

for i in $(seq 1 "$REPEATS"); do
  LOG="$OUT/auth_v2_repeat_${i}.log"

  set +e
  START_NS="$(date +%s%N)"
  "$PYTHON_BIN" "$ROOT/$found" >"$LOG" 2>&1
  RC=$?
  END_NS="$(date +%s%N)"
  set -e

  DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))

  python3 - <<PY >> "$OUT/timing_rows.jsonl"
import json
print(json.dumps({
  "repeat": $i,
  "runner": "$found",
  "exit_code": $RC,
  "duration_ms": $DURATION_MS,
  "log_path": "$LOG"
}))
PY
done

python3 - <<PY
import json, pathlib, statistics, time

out = pathlib.Path("$OUT")
rows = [json.loads(x) for x in (out / "timing_rows.jsonl").read_text().splitlines() if x.strip()]
ok = [r for r in rows if r["exit_code"] == 0]
dur = [r["duration_ms"] for r in ok]

summary = {
  "status": "DIRECT_AUTH_V2_TIMING_COLLECTED" if ok else "AUTH_V2_TIMING_RUNNER_FAILED",
  "runner": "$found",
  "requested_repeats": int("$REPEATS"),
  "successful_repeats": len(ok),
  "mean_duration_ms": statistics.mean(dur) if dur else None,
  "p50_duration_ms": statistics.median(dur) if dur else None,
  "min_duration_ms": min(dur) if dur else None,
  "max_duration_ms": max(dur) if dur else None,
  "claim_boundary": "This timing covers the detected AUTH_V2.x runner only. It is not full 240-row prover coverage unless explicitly repeated and mapped for every Full-L4 row.",
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

path = pathlib.Path("$SUMMARY")
path.write_text(json.dumps(summary, indent=2) + "\n")
PY

cat "$SUMMARY"
