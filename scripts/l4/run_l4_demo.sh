#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate

mkdir -p artifacts/out_l4
mkdir -p artifacts/out_l4/traces
mkdir -p logs/l4

NDJSON_OUT="artifacts/out_l4/demo_run.ndjson"

log_event() {
  local stage="$1"
  local status="$2"
  local detail="$3"

  python3 - "$stage" "$status" "$detail" "$NDJSON_OUT" <<'PY'
import json
import sys
import time

stage = sys.argv[1]
status = sys.argv[2]
detail = sys.argv[3]
out_file = sys.argv[4]

event = {
    "timestamp": int(time.time()),
    "stage": stage,
    "status": status,
    "detail": detail,
}

with open(out_file, "a") as f:
    f.write(json.dumps(event) + "\n")
PY
}

echo "[L4 demo] refresh capabilities"
python3 scripts/l4/refresh_capabilities.py
log_event "refresh_capabilities" "ok" "fresh short-lived capabilities issued"

echo "[L4 demo] export registered agents"
python3 scripts/l4/export_registered_agents.py
log_event "export_registered_agents" "ok" "registered_agents.localhost.json refreshed"

echo "[L4 demo] create trace bundle"
python3 scripts/l4/create_trace_bundle.py
log_event "create_trace_bundle" "ok" "trace bundle created"

echo "[L4 demo] pin trace bundle to IPFS"
python3 scripts/l4/pin_trace_bundle.py
CID="$(python3 - <<'PY'
import json
with open("artifacts/out_l4/traces/trace_bundle.task-0001.cid.json", "r") as f:
    data = json.load(f)
print(data["cid"])
PY
)"
log_event "pin_trace_bundle" "ok" "cid=${CID}"

echo "[L4 demo] create anomaly bundle"
python3 scripts/l4/create_anomaly_bundle.py
log_event "create_anomaly_bundle" "ok" "anomaly bundle created"

echo "[L4 demo] gateway health"
HEALTH="$(curl -s http://127.0.0.1:8081/health)"
echo "$HEALTH" | tee logs/l4/gateway_health.json
log_event "gateway_health" "ok" "$HEALTH"

echo "[L4 demo] report anomaly to gateway"
ANOM_RESP="$(curl -s -X POST http://127.0.0.1:8081/anomaly/report \
  -H "Content-Type: application/json" \
  --data @artifacts/out_l4/traces/anomaly_bundle.task-0001.json)"
echo "$ANOM_RESP" | tee logs/l4/anomaly_report.json
log_event "anomaly_report" "ok" "$ANOM_RESP"

echo "[L4 demo] submit mock decision"
DECISION_OUT="$(python3 scripts/l4/submit_agent_decision_mock.py)"
echo "$DECISION_OUT" | tee logs/l4/mock_decision.txt
log_event "submit_mock_decision" "ok" "$DECISION_OUT"

echo
echo "=== L4 DEMO SUMMARY ==="
echo "CID: $CID"
echo "$DECISION_OUT"
echo
echo "NDJSON log -> $NDJSON_OUT"
echo "Logs directory -> logs/l4"
