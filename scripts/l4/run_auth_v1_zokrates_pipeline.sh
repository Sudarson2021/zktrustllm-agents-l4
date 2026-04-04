#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate

LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4"
mkdir -p "$LOG_DIR" "$OUT_DIR"

PIPELINE_LOG="$OUT_DIR/auth_v1_pipeline.ndjson"

log_event() {
  local stage="$1"
  local status="$2"
  local detail="$3"

  python3 - "$stage" "$status" "$detail" "$PIPELINE_LOG" <<'PY'
import json
import sys
import time
from pathlib import Path

stage, status, detail, outfile = sys.argv[1:]
record = {
    "timestamp": int(time.time()),
    "stage": stage,
    "status": status,
    "detail": detail,
}
path = Path(outfile)
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, "a") as f:
    f.write(json.dumps(record) + "\n")
PY
}

echo "[AUTH_V1 pipeline] validate interface"
python3 scripts/l4/validate_auth_v1_circuit_interface.py
log_event "validate_interface" "ok" "circuit/template/witness order match"

echo "[AUTH_V1 pipeline] compile skeleton"
scripts/l4/compile_auth_v1_zokrates.sh
log_event "compile" "ok" "compile skeleton executed"

echo "[AUTH_V1 pipeline] witness skeleton"
scripts/l4/run_auth_v1_zokrates_witness.sh
log_event "witness" "ok" "witness skeleton executed"

echo "[AUTH_V1 pipeline] proof skeleton"
scripts/l4/run_auth_v1_zokrates_proof.sh
log_event "proof" "ok" "proof skeleton executed"

echo
echo "=== AUTH_V1 PIPELINE SUMMARY ==="
echo "Pipeline log -> $PIPELINE_LOG"
echo "Compile log   -> logs/l4/zokrates_compile_status.txt"
echo "Witness log   -> logs/l4/zokrates_witness_status.txt"
echo "Proof log     -> logs/l4/zokrates_proof_status.txt"
