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
RPC_URL="${RPC_URL:-http://127.0.0.1:8545}"

HARDHAT_STARTED=0
HARDHAT_LOG="$OUT/hardhat_node.log"

cleanup() {
  if [ "$HARDHAT_STARTED" -eq 1 ] && [ -n "${HARDHAT_PID:-}" ]; then
    kill "$HARDHAT_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

write_json_status() {
  local status="$1"
  local boundary="$2"
  "$PYTHON_BIN" - <<PY
import json, pathlib, time
path = pathlib.Path("$SUMMARY")
path.write_text(json.dumps({
  "status": "$status",
  "requested_repeats": int("$REPEATS"),
  "successful_repeats": 0,
  "mean_duration_ms": None,
  "p50_duration_ms": None,
  "min_duration_ms": None,
  "max_duration_ms": None,
  "claim_boundary": "$boundary",
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}, indent=2) + "\n")
PY
}

echo "[AUTH_V2.2] using python: $PYTHON_BIN"

"$PYTHON_BIN" - <<'PY' || {
import importlib.util, sys
missing = [m for m in ["web3", "eth_account", "hexbytes"] if importlib.util.find_spec(m) is None]
if missing:
    print("Missing Python modules:", ",".join(missing), file=sys.stderr)
    raise SystemExit(1)
PY
  write_json_status "PYTHON_DEPENDENCIES_MISSING" "Install requirements-paper258.txt in .venv-paper258 before claiming AUTH_V2.x timing."
  cat "$SUMMARY"
  exit 0
}

# Start Hardhat node if localhost RPC is not responding.
if ! "$PYTHON_BIN" - <<PY >/dev/null 2>&1
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("$RPC_URL"))
raise SystemExit(0 if w3.is_connected() else 1)
PY
then
  echo "[AUTH_V2.2] starting local Hardhat node"
  (cd "$ROOT" && npx hardhat node >"$HARDHAT_LOG" 2>&1) &
  HARDHAT_PID=$!
  HARDHAT_STARTED=1

  for _ in $(seq 1 40); do
    if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("$RPC_URL"))
raise SystemExit(0 if w3.is_connected() else 1)
PY
    then
      break
    fi
    sleep 1
  done
fi

if ! "$PYTHON_BIN" - <<PY >/dev/null 2>&1
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("$RPC_URL"))
raise SystemExit(0 if w3.is_connected() else 1)
PY
then
  write_json_status "LOCAL_CHAIN_UNAVAILABLE" "Hardhat localhost RPC was unavailable, so AUTH_V2.2 timing is not claimable from this run."
  cat "$SUMMARY"
  exit 0
fi

# Ensure contracts are compiled.
(cd "$ROOT" && npx hardhat compile >/dev/null 2>"$OUT/hardhat_compile.stderr.log") || {
  write_json_status "HARDHAT_COMPILE_FAILED" "Could not compile verifier artifacts; AUTH_V2.2 timing remains bounded/missing."
  cat "$SUMMARY"
  exit 0
}

# Check whether deployment address has bytecode; redeploy if stale.
NEEDS_DEPLOY="$("$PYTHON_BIN" - <<PY
import json
from pathlib import Path
from web3 import Web3

root = Path("$ROOT")
dep_path = root / "deployments" / "l4.localhost.json"
w3 = Web3(Web3.HTTPProvider("$RPC_URL"))

needs = True
if dep_path.exists():
    dep = json.loads(dep_path.read_text())
    addr = dep.get("authV2_2Groth16Verifier")
    if addr:
        try:
            code = w3.eth.get_code(Web3.to_checksum_address(addr))
            needs = len(code) == 0
        except Exception:
            needs = True
print("1" if needs else "0")
PY
)"

if [ "$NEEDS_DEPLOY" = "1" ]; then
  echo "[AUTH_V2.2] deploying verifier to current localhost chain"
  (cd "$ROOT" && npx hardhat run scripts/l4/zk/deploy_auth_v2_2_localhost.js --network localhost >"$OUT/auth_v2_2_deploy.stdout.log" 2>"$OUT/auth_v2_2_deploy.stderr.log") || {
    write_json_status "AUTH_V2_2_LOCAL_DEPLOY_FAILED" "Could not deploy AUTH_V2.2 verifier to localhost; AUTH_V2.x timing remains bounded/missing."
    cat "$SUMMARY"
    exit 0
  }
fi

found="scripts/l4/check_auth_v2_2_groth16_verifier.py"

if [ ! -f "$ROOT/$found" ]; then
  write_json_status "NO_AUTH_V2_RUNNER_FOUND" "Do not claim complete AUTH_V2.x prover timing. Report as missing or partial future work."
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

  "$PYTHON_BIN" - <<PY >> "$OUT/timing_rows.jsonl"
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

"$PYTHON_BIN" - <<PY
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
  "claim_boundary": "This timing covers the detected AUTH_V2.2 verifier call on a local ephemeral Hardhat chain. It is not full 240-row prover coverage unless explicitly repeated and mapped for every Full-L4 row.",
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

path = pathlib.Path("$SUMMARY")
path.write_text(json.dumps(summary, indent=2) + "\n")
PY

cat "$SUMMARY"
