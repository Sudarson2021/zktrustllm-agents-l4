#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT_DIR="results/l4_persistent_hardhat_anchor"
mkdir -p "$OUT_DIR"

NODE_LOG="$OUT_DIR/hardhat_node_stdout.log"
NODE_ERR="$OUT_DIR/hardhat_node_stderr.log"
NODE_PID_FILE="$OUT_DIR/hardhat_node.pid"

RPC_URL="http://127.0.0.1:8545"
STARTED_NODE=0

rpc_check() {
python3 - <<'PY'
import json
import sys
import urllib.request

payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "eth_chainId",
    "params": []
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8545",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=1) as r:
        r.read()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
}

cleanup() {
  if [ "${STARTED_NODE}" = "1" ] && [ -f "$NODE_PID_FILE" ]; then
    PID="$(cat "$NODE_PID_FILE")"
    if kill -0 "$PID" >/dev/null 2>&1; then
      kill "$PID" >/dev/null 2>&1 || true
      sleep 1
      kill -9 "$PID" >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT

if rpc_check; then
  echo "[step109] Existing Hardhat-compatible RPC is reachable at $RPC_URL"
else
  echo "[step109] Starting persistent local Hardhat node at $RPC_URL"
  npx hardhat node --hostname 127.0.0.1 --port 8545 >"$NODE_LOG" 2>"$NODE_ERR" &
  echo "$!" > "$NODE_PID_FILE"
  STARTED_NODE=1

  for i in $(seq 1 30); do
    if rpc_check; then
      echo "[step109] Hardhat node is ready"
      break
    fi
    sleep 1
  done

  if ! rpc_check; then
    echo "[step109] ERROR: Hardhat node did not become ready"
    exit 1
  fi
fi

echo "[step109] Compiling contracts"
npx hardhat compile

echo "[step109] Running persistent Hardhat audit-anchor validation"
L4_HARDHAT_RPC_URL="$RPC_URL" npx hardhat run --network localhost scripts/l4/validate_l4_audit_anchor_persistent_hardhat.js

echo "[step109] Done"
