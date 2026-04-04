#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

CIRCUIT_FILE="circuits/auth_v1.zok"
LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4/zokrates_compile"
mkdir -p "$LOG_DIR" "$OUT_DIR"

CMD_LOG="$LOG_DIR/zokrates_compile_command.txt"
STATUS_LOG="$LOG_DIR/zokrates_compile_status.txt"

OUT_BIN="$OUT_DIR/auth_v1.out"
CMD="zokrates compile -i $CIRCUIT_FILE -o $OUT_BIN"

if [ ! -f "$CIRCUIT_FILE" ]; then
  echo "Missing circuit file: $CIRCUIT_FILE" >&2
  exit 1
fi

echo "$CMD" > "$CMD_LOG"
echo "[ZoKrates compile] command saved -> $CMD_LOG"

if ! command -v zokrates >/dev/null 2>&1; then
  echo "ZoKrates not installed. Skeleton only; command recorded." | tee "$STATUS_LOG"
  exit 0
fi

echo "[ZoKrates compile] running compile"
set +e
zokrates compile -i "$CIRCUIT_FILE" -o "$OUT_BIN" | tee "$LOG_DIR/zokrates_compile.out"
RC=$?
set -e

if [ $RC -ne 0 ]; then
  echo "compile failed with exit code $RC" | tee "$STATUS_LOG"
  exit $RC
fi

echo "compile completed successfully" | tee "$STATUS_LOG"
echo "compiled output -> $OUT_BIN"
