#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4"
mkdir -p "$LOG_DIR" "$OUT_DIR"

PIPELINE_LOG="$OUT_DIR/auth_v1_groth16_repro.ndjson"
: > "$PIPELINE_LOG"

log_event() {
  local stage="$1"
  local status="$2"
  local detail="$3"
  python3 - "$stage" "$status" "$detail" "$PIPELINE_LOG" <<'PY'
import json
import sys
from pathlib import Path
import time

stage, status, detail, out = sys.argv[1:]
record = {
    "timestamp": int(time.time()),
    "stage": stage,
    "status": status,
    "detail": detail,
}
with open(Path(out), "a") as f:
    f.write(json.dumps(record) + "\n")
PY
}

run_stage() {
  local name="$1"
  shift
  echo "[AUTH_V1 repro] $name"
  "$@" | tee "$LOG_DIR/${name}.out"
  log_event "$name" "ok" "completed"
}

run_stage build_payload python3 scripts/l4/build_auth_v1_proof_payload.py
run_stage build_circuit_input python3 scripts/l4/build_auth_v1_circuit_input.py
run_stage docker_proof scripts/l4/run_auth_v1_zokrates_docker.sh

cp artifacts/out_l4/zokrates_docker/proof.json artifacts/out_l4/zokrates_docker/proof.frozen.json
log_event freeze_proof ok "proof.json copied to proof.frozen.json"

run_stage positive_verifier python3 scripts/l4/check_auth_v1_groth16_verifier.py
run_stage positive_wrapper python3 scripts/l4/check_auth_v1_wrapper_groth16.py
run_stage positive_submit python3 scripts/l4/direct_submit_auth_v1_groth16.py

run_stage build_bad_proof python3 scripts/l4/build_auth_v1_bad_groth16_proof.py
run_stage negative_verifier python3 scripts/l4/check_auth_v1_groth16_verifier_bad.py
run_stage negative_wrapper python3 scripts/l4/check_auth_v1_wrapper_groth16_bad.py
run_stage negative_submit python3 scripts/l4/direct_submit_auth_v1_groth16_bad.py

echo
echo "=== AUTH_V1 GROTH16 REPRO SUMMARY ==="
echo "Pipeline log -> $PIPELINE_LOG"
echo "Positive verifier log -> $LOG_DIR/positive_verifier.out"
echo "Positive wrapper log  -> $LOG_DIR/positive_wrapper.out"
echo "Positive submit log   -> $LOG_DIR/positive_submit.out"
echo "Negative verifier log -> $LOG_DIR/negative_verifier.out"
echo "Negative wrapper log  -> $LOG_DIR/negative_wrapper.out"
echo "Negative submit log   -> $LOG_DIR/negative_submit.out"
