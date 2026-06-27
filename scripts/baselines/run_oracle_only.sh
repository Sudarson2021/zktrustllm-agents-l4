#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/artifacts/out"
LOG="$OUT/logs"

TENANTS="${TENANTS:-10}"
RUNS="${RUNS:-5}"
N="${N:-$((TENANTS * RUNS))}"

mkdir -p "$OUT/baseline_oracle_only" "$LOG"

if ! lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[RUN] starting hardhat node for oracle-only baseline..."
  (cd "$ROOT" && nohup npx hardhat node >"$LOG/hardhat_node_oracle_only.log" 2>&1 &)
  for _ in {1..40}; do
    if lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
      echo "[OK] hardhat up"
      break
    fi
    sleep 0.25
  done
fi

if ! lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[ERR] hardhat failed for oracle-only baseline. See $LOG/hardhat_node_oracle_only.log"
  exit 1
fi

echo "[Baseline] Oracle-only real NDJSON baseline: N=$N"

(
  cd "$ROOT"
  N="$N" \
  NDJSON_OUT="$OUT/baseline_oracle_only/results.ndjson" \
  npx hardhat run scripts/baselines/oracle_only_ndjson.js --network localhost
) | tee "$LOG/b1_wrapper.log"

test -s "$OUT/baseline_oracle_only/results.ndjson"
echo "[OK] oracle-only output: $OUT/baseline_oracle_only/results.ndjson"
wc -l "$OUT/baseline_oracle_only/results.ndjson"
