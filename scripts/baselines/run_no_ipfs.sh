#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/artifacts/out"
LOG="$OUT/logs"

TENANTS="${TENANTS:-10}"
RUNS="${RUNS:-5}"

mkdir -p "$OUT/baseline_no_ipfs" "$OUT/evidence" "$LOG"

if ! lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[RUN] starting hardhat node for no-IPFS baseline..."
  (cd "$ROOT" && nohup npx hardhat node >"$LOG/hardhat_node_no_ipfs.log" 2>&1 &)
  for _ in {1..40}; do
    if lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
      echo "[OK] hardhat up"
      break
    fi
    sleep 0.25
  done
fi

if ! lsof -iTCP:8545 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[ERR] hardhat failed for no-IPFS baseline. See $LOG/hardhat_node_no_ipfs.log"
  exit 1
fi

echo "[Baseline] No-IPFS real NDJSON baseline: TENANTS=$TENANTS RUNS=$RUNS"

(
  cd "$ROOT"
  TENANTS="$TENANTS" \
  RUNS="$RUNS" \
  MODE="no_ipfs" \
  NDJSON_OUT="$OUT/baseline_no_ipfs/tenants_results.ndjson" \
  EVID_DIR="$OUT/evidence" \
  npx hardhat run scripts/tenants/run_tenants_ndjson.js --network localhost
) | tee "$LOG/b2_wrapper.log"

test -s "$OUT/baseline_no_ipfs/tenants_results.ndjson"
echo "[OK] no-IPFS output: $OUT/baseline_no_ipfs/tenants_results.ndjson"
wc -l "$OUT/baseline_no_ipfs/tenants_results.ndjson"
