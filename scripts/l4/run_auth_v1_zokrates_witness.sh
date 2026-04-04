#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

INPUT_JSON="artifacts/out_l4/zokrates_input.auth_v1.json"
LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4/zokrates_run"
mkdir -p "$LOG_DIR" "$OUT_DIR"

CMD_LOG="$LOG_DIR/zokrates_witness_command.txt"
STATUS_LOG="$LOG_DIR/zokrates_witness_status.txt"
ARGS_FILE="$OUT_DIR/auth_v1.flat_args.txt"

if [ ! -f "$INPUT_JSON" ]; then
  echo "Missing input file: $INPUT_JSON" >&2
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

inp = Path("artifacts/out_l4/zokrates_input.auth_v1.json")
out = Path("artifacts/out_l4/zokrates_run/auth_v1.flat_args.txt")

with open(inp, "r") as f:
    data = json.load(f)

args = data["flatArguments"]
out.write_text(" ".join(args))
print(f"Wrote flat args -> {out}")
print(f"Argument count -> {len(args)}")
PY

ARGS="$(cat "$ARGS_FILE")"
CMD="zokrates compute-witness -a $ARGS"

echo "$CMD" > "$CMD_LOG"
echo "[ZoKrates witness] command saved -> $CMD_LOG"

if ! command -v zokrates >/dev/null 2>&1; then
  echo "ZoKrates not installed. Skeleton only; command recorded." | tee "$STATUS_LOG"
  exit 0
fi

echo "[ZoKrates witness] running compute-witness"
set +e
zokrates compute-witness -a $ARGS | tee "$LOG_DIR/zokrates_compute_witness.out"
RC=$?
set -e

if [ $RC -ne 0 ]; then
  echo "compute-witness failed with exit code $RC" | tee "$STATUS_LOG"
  exit $RC
fi

echo "compute-witness completed successfully" | tee "$STATUS_LOG"
