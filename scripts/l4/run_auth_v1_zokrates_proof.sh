#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4/zokrates_run"
mkdir -p "$LOG_DIR" "$OUT_DIR"

CMD_LOG="$LOG_DIR/zokrates_proof_command.txt"
STATUS_LOG="$LOG_DIR/zokrates_proof_status.txt"

CMD="zokrates generate-proof"

echo "$CMD" > "$CMD_LOG"
echo "[ZoKrates proof] command saved -> $CMD_LOG"

if ! command -v zokrates >/dev/null 2>&1; then
  echo "ZoKrates not installed. Skeleton only; command recorded." | tee "$STATUS_LOG"
  exit 0
fi

echo "[ZoKrates proof] running generate-proof"
set +e
zokrates generate-proof | tee "$LOG_DIR/zokrates_generate_proof.out"
RC=$?
set -e

if [ $RC -ne 0 ]; then
  echo "generate-proof failed with exit code $RC" | tee "$STATUS_LOG"
  exit $RC
fi

echo "generate-proof completed successfully" | tee "$STATUS_LOG"
