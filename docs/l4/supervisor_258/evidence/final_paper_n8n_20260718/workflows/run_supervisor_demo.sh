#!/usr/bin/env bash
set -Eeuo pipefail

# ZKTrustLLM-Agents L4 supervisor demonstration
#
# Runs ONE live n8n cell and then displays the already-frozen 180-cell
# benchmark summary. It does not rerun or alter the frozen R10 benchmark.
#
# Usage:
#   bash run_supervisor_demo.sh [SCENARIO_ID] [MODE] [APPROVE_REVIEW]
#
# Examples:
#   bash run_supervisor_demo.sh S2 AGENTIC_RAG yes
#   bash run_supervisor_demo.sh S4 AGENTIC_RAG no
#
# Supported modes:
#   NO_RAG, RAG, AGENTIC_RAG

REPO_ROOT="${REPO_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
N8N_URL="${N8N_URL:-http://127.0.0.1:5678}"
GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:18080}"

SCENARIO_ID="${1:-S2}"
MODE="${2:-AGENTIC_RAG}"
APPROVE_REVIEW="${3:-yes}"

FINAL_EXP_ID="${FINAL_EXP_ID:-l4_oracle_20260716T131803Z_r10}"
FINAL_EXP_DIR="$REPO_ROOT/runtime/experiments/$FINAL_EXP_ID"
DEMO_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEMO_DIR="$REPO_ROOT/runtime/supervisor_demo/$DEMO_STAMP"
WEBHOOK_URL="$N8N_URL/webhook/l4-final-paper-demo"
REVIEW_URL="$N8N_URL/webhook/l4-action-review"

mkdir -p "$DEMO_DIR"

log() {
  printf '\n\033[1;36m[%s]\033[0m %s\n' "$(date -u +%H:%M:%S)" "$*"
}

fail() {
  printf '\n\033[1;31mERROR:\033[0m %s\n' "$*" >&2
  exit 1
}

on_error() {
  local rc=$?
  printf '\n\033[1;31mDemo failed with exit code %s.\033[0m\n' "$rc" >&2
  if [[ -d "$REPO_ROOT" ]]; then
    (
      cd "$REPO_ROOT"
      docker compose ps > "$DEMO_DIR/docker_compose_ps_failure.txt" 2>&1 || true

      SERVICES="$(docker compose config --services 2>/dev/null || true)"
      LOG_SERVICES=()

      for candidate in gateway n8n-main n8n n8n-worker-1 n8n-worker-2; do
        if grep -qx "$candidate" <<<"$SERVICES"; then
          LOG_SERVICES+=("$candidate")
        fi
      done

      if ((${#LOG_SERVICES[@]})); then
        docker compose logs \
          --no-color \
          --since 15m \
          --tail 500 \
          "${LOG_SERVICES[@]}" \
          > "$DEMO_DIR/docker_logs_failure.txt" 2>&1 || true
      fi
    )
  fi
  printf 'Failure diagnostics: %s\n' "$DEMO_DIR" >&2
  exit "$rc"
}

trap on_error ERR

command -v curl >/dev/null || fail "curl is required."
command -v python3 >/dev/null || fail "python3 is required."
command -v docker >/dev/null || fail "docker is required."
command -v timeout >/dev/null || fail "GNU timeout is required."

[[ -d "$REPO_ROOT" ]] || fail "Repository not found: $REPO_ROOT"
cd "$REPO_ROOT"

case "$MODE" in
  NO_RAG|RAG|AGENTIC_RAG) ;;
  *) fail "Unsupported mode: $MODE" ;;
esac

case "$SCENARIO_ID" in
  S1)
    SCENARIO_FILE="scenarios/configs/S1_compliant_baseline.json"
    SCENARIO_TITLE="Compliant O-CU baseline"
    EXPECTED_DECISION="COMPLIANT"
    EXPECTED_ACTION="HUMAN"
    ;;
  S2)
    SCENARIO_FILE="scenarios/configs/S2_drb_integrity_disabled.json"
    SCENARIO_TITLE="DRB integrity disabled"
    EXPECTED_DECISION="NON_COMPLIANT"
    EXPECTED_ACTION="HUMAN"
    ;;
  S3)
    SCENARIO_FILE="scenarios/configs/S3_legacy_o1_tls.json"
    SCENARIO_TITLE="Legacy TLS on O1 management path"
    EXPECTED_DECISION="NON_COMPLIANT"
    EXPECTED_ACTION="HUMAN"
    ;;
  S4)
    SCENARIO_FILE="scenarios/configs/S4_unauthorised_xapp_actuation.json"
    SCENARIO_TITLE="Unauthorised xApp actuation attempt"
    EXPECTED_DECISION="NON_COMPLIANT"
    EXPECTED_ACTION="NEVER"
    ;;
  S5)
    SCENARIO_FILE="scenarios/configs/S5_replayed_anchor.json"
    SCENARIO_TITLE="Replayed audit-anchor commitment"
    EXPECTED_DECISION="NON_COMPLIANT"
    EXPECTED_ACTION="NEVER"
    ;;
  S6)
    SCENARIO_FILE="scenarios/configs/S6_insufficient_evidence.json"
    SCENARIO_TITLE="Insufficient evidence and unsafe immediate actuation"
    EXPECTED_DECISION="UNCERTAIN"
    EXPECTED_ACTION="HUMAN"
    ;;
  *)
    fail "Unsupported scenario: $SCENARIO_ID"
    ;;
esac

[[ -f "$SCENARIO_FILE" ]] || fail "Scenario file missing: $SCENARIO_FILE"

log "Starting the self-hosted L4 stack"
docker compose up -d

log "Container status"
docker compose ps | tee "$DEMO_DIR/docker_compose_ps.txt"

log "Waiting for the gateway"
GATEWAY_OK=0
for _ in $(seq 1 60); do
  if curl -fsS "$GATEWAY_URL/health" > "$DEMO_DIR/gateway_health.json" 2>/dev/null; then
    GATEWAY_OK=1
    break
  fi
  sleep 2
done
[[ "$GATEWAY_OK" -eq 1 ]] || fail "Gateway did not become healthy."

python3 -m json.tool \
  "$DEMO_DIR/gateway_health.json" \
  | tee "$DEMO_DIR/gateway_health_pretty.json"

log "Checking the n8n user interface"
curl -fsS --max-time 20 "$N8N_URL" >/dev/null \
  || fail "n8n is not reachable at $N8N_URL"

log "Running live provider, embedding and OPA preflight"
curl -fsS \
  --max-time 180 \
  -X POST \
  "$GATEWAY_URL/v1/preflight" \
  -H 'Content-Type: application/json' \
  -d '{"live_smoke":true}' \
  > "$DEMO_DIR/preflight.json"

python3 -m json.tool \
  "$DEMO_DIR/preflight.json" \
  | tee "$DEMO_DIR/preflight_pretty.json"

python3 - "$DEMO_DIR/preflight.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))

if data.get("ok") is not True:
    raise SystemExit("Preflight did not return ok=true.")

smoke = data.get("live_smoke", {})
failed = [
    name
    for name, result in smoke.items()
    if result.get("ok") is not True
]

if failed:
    raise SystemExit(
        "Provider smoke checks failed: " + ", ".join(failed)
    )

print("PASS: all configured live provider smoke checks succeeded.")
PY

log "Preparing the one-cell live demo payload"
python3 - \
  "$SCENARIO_FILE" \
  "$SCENARIO_TITLE" \
  "$SCENARIO_ID" \
  "$MODE" \
  "$EXPECTED_DECISION" \
  "$EXPECTED_ACTION" \
  "$DEMO_DIR/request.json" <<'PY'
import json
import sys
from pathlib import Path

scenario_path = Path(sys.argv[1])
title = sys.argv[2]
scenario_id = sys.argv[3]
mode = sys.argv[4]
expected_decision = sys.argv[5]
expected_action = sys.argv[6]
output_path = Path(sys.argv[7])

scenario = json.loads(
    scenario_path.read_text(encoding="utf-8")
)

payload = {
    "config_text": json.dumps(
        scenario,
        sort_keys=True,
        separators=(",", ":"),
    ),
    "scenario": title,
    "retrieval_mode": mode,
    "metadata": {
        "source": "terminal_supervisor_demo",
        "paper": "ZKTrustLLM-Agents L4",
        "scenario_id": scenario_id,
        "expected_oracle_decision": expected_decision,
        "expected_oracle_action_class": expected_action,
        "expert_verified": False,
        "oracle_relative": True,
        "demo_only": True,
    },
}

output_path.write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps({
    "scenario_id": scenario_id,
    "scenario": title,
    "retrieval_mode": mode,
    "expected_oracle_decision": expected_decision,
    "expected_oracle_action_class": expected_action,
    "request_file": str(output_path),
}, indent=2))
PY

log "Triggering the active n8n production webhook"
log "This one Agentic-RAG run may take roughly 2-4 minutes."

HTTP_CODE="$(
  curl -sS \
    --max-time 1200 \
    -o "$DEMO_DIR/webhook_response.json" \
    -w '%{http_code}' \
    -X POST \
    "$WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    --data-binary "@$DEMO_DIR/request.json"
)"

printf 'n8n HTTP status: %s\n' "$HTTP_CODE" \
  | tee "$DEMO_DIR/webhook_http_status.txt"

if [[ ! "$HTTP_CODE" =~ ^2 ]]; then
  cat "$DEMO_DIR/webhook_response.json" || true

  if [[ "$HTTP_CODE" == "404" ]]; then
    fail "Webhook is not registered. Activate the four provider workflows and the paper master workflow in n8n."
  fi

  fail "The n8n workflow returned HTTP $HTTP_CODE."
fi

python3 -m json.tool \
  "$DEMO_DIR/webhook_response.json" \
  | tee "$DEMO_DIR/webhook_response_pretty.json"

RUN_ID="$(
  python3 - "$DEMO_DIR/webhook_response.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))

def find_run_id(value):
    if isinstance(value, dict):
        run_id = value.get("run_id")
        if isinstance(run_id, str) and run_id:
            return run_id
        for item in value.values():
            found = find_run_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_run_id(item)
            if found:
                return found
    return None

run_id = find_run_id(data)

if not run_id:
    raise SystemExit(2)

print(run_id)
PY
)" || fail "The webhook response did not contain a run_id."

printf '%s\n' "$RUN_ID" > "$DEMO_DIR/run_id.txt"
log "Live run ID: $RUN_ID"

REPORT_PATH="$REPO_ROOT/runtime/evidence/$RUN_ID/final_report.json"

log "Waiting for the final anchored report"
REPORT_OK=0
for _ in $(seq 1 60); do
  if [[ -s "$REPORT_PATH" ]]; then
    REPORT_OK=1
    break
  fi
  sleep 2
done
[[ "$REPORT_OK" -eq 1 ]] || fail "Final report not found: $REPORT_PATH"

cp -a "$REPORT_PATH" "$DEMO_DIR/final_report.json"

log "Scientific live-run summary"
python3 - "$REPORT_PATH" <<'PY'
import json
import sys
from datetime import datetime

report = json.load(open(sys.argv[1], encoding="utf-8"))

providers = report.get("providers", {})
roles = report.get("role_chain", {})

provider_valid = sum(
    1
    for item in providers.values()
    if item.get("provider_call_succeeded") is True
    and item.get("valid_json") is True
    and (item.get("deterministic_validation") or {}).get("valid") is True
)

role_valid = sum(
    1
    for item in roles.values()
    if item.get("valid_json") is True
    and (item.get("deterministic_validation") or {}).get("valid") is True
)

created = report.get("created_at")
reported = report.get("reported_at")
elapsed = None

try:
    if created and reported:
        elapsed = (
            datetime.fromisoformat(reported)
            - datetime.fromisoformat(created)
        ).total_seconds()
except Exception:
    pass

summary = {
    "run_id": report.get("run_id"),
    "status": report.get("status"),
    "execution_mode": report.get("execution_mode"),
    "retrieval_mode": (
        report.get("metadata", {}).get("retrieval_mode")
        or report.get("retrieval", {}).get("retrieval_mode")
    ),
    "final_decision": (
        report.get("reflection", {}).get("final_decision")
        or report.get("decision")
    ),
    "enforced_action_class": report.get("policy", {}).get(
        "enforced_action_class"
    ),
    "automatic_execution_enabled": report.get("policy", {}).get(
        "automatic_execution_enabled"
    ),
    "provider_validation": f"{provider_valid}/{len(providers)}",
    "role_chain_validation": f"{role_valid}/{len(roles)}",
    "report_hash": report.get("report_hash"),
    "wall_clock_seconds_from_report": elapsed,
    "claim_boundary": (
        "Synthetic experimental operator-policy conformance only; "
        "not independent expert verification or production O-RAN actuation."
    ),
}

print(json.dumps(summary, indent=2))
PY

ACTION_CLASS="$(
  python3 - "$REPORT_PATH" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
print(report.get("policy", {}).get("enforced_action_class", ""))
PY
)"

if [[ "$APPROVE_REVIEW" == "yes" ]] \
  && [[ "$ACTION_CLASS" == "HUMAN" || "$ACTION_CLASS" == "PRIVILEGED" ]]; then

  if [[ "$ACTION_CLASS" == "PRIVILEGED" ]]; then
    REVIEWER_ROLE="privileged_operator"
  else
    REVIEWER_ROLE="mno_approver"
  fi

  log "Submitting the bounded human-review decision"

  python3 - \
    "$RUN_ID" \
    "$REVIEWER_ROLE" \
    "$DEMO_DIR/review_request.json" <<'PY'
import json
import sys
from pathlib import Path

run_id = sys.argv[1]
role = sys.argv[2]
path = Path(sys.argv[3])

payload = {
    "run_id": run_id,
    "reviewer_id": "supervisor-demo-reviewer",
    "reviewer_role": role,
    "approved": True,
    "rationale": (
        "Approved only for the bounded dry-run simulated action ledger "
        "during the supervisor demonstration."
    ),
}

path.write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)
PY

  REVIEW_HTTP="$(
    curl -sS \
      --max-time 300 \
      -o "$DEMO_DIR/review_response.json" \
      -w '%{http_code}' \
      -X POST \
      "$REVIEW_URL" \
      -H 'Content-Type: application/json' \
      --data-binary "@$DEMO_DIR/review_request.json"
  )"

  printf 'Review webhook HTTP status: %s\n' "$REVIEW_HTTP" \
    | tee "$DEMO_DIR/review_http_status.txt"

  python3 -m json.tool \
    "$DEMO_DIR/review_response.json" \
    | tee "$DEMO_DIR/review_response_pretty.json"

  [[ "$REVIEW_HTTP" =~ ^2 ]] \
    || fail "The human-review callback returned HTTP $REVIEW_HTTP."
else
  log "No human-review callback submitted"
  printf 'Action class: %s\n' "$ACTION_CLASS"
  printf 'Requested review submission: %s\n' "$APPROVE_REVIEW"
fi

log "Displaying the frozen 180-cell benchmark summary"
SUMMARY_FILE="$FINAL_EXP_DIR/analysis_oracle_final/summary_by_mode.csv"

if [[ -f "$SUMMARY_FILE" ]]; then
  python3 - "$SUMMARY_FILE" <<'PY'
import csv
import sys

rows = list(
    csv.DictReader(
        open(sys.argv[1], newline="", encoding="utf-8")
    )
)

headers = [
    "Mode",
    "Decision",
    "Action",
    "Coverage",
    "Provider val.",
    "Role val.",
    "Median s",
    "P95 s",
]

values = []

for row in rows:
    def pct(name):
        value = row.get(name, "")
        return (
            "N/A"
            if value in ("", None)
            else f"{100 * float(value):.1f}%"
        )

    values.append([
        row["retrieval_mode"],
        pct("decision_accuracy"),
        pct("enforced_action_accuracy"),
        pct("coverage"),
        pct("provider_validation_rate"),
        pct("role_validation_rate"),
        f"{float(row['latency_median_sec']):.3f}",
        f"{float(row['latency_p95_sec']):.3f}",
    ])

widths = [
    max(len(headers[i]), *(len(row[i]) for row in values))
    for i in range(len(headers))
]

def line(row):
    return " | ".join(
        cell.ljust(widths[i])
        for i, cell in enumerate(row)
    )

print(line(headers))
print("-+-".join("-" * width for width in widths))

for row in values:
    print(line(row))
PY
else
  echo "Frozen summary not found: $SUMMARY_FILE"
fi

log "Demo completed successfully"
printf 'Demo evidence directory: %s\n' "$DEMO_DIR"
printf 'Live run evidence: %s\n' "$REPO_ROOT/runtime/evidence/$RUN_ID"
printf 'Open n8n at: %s\n' "$N8N_URL"
printf 'In n8n, open Overview -> Executions to display the live node-by-node trace.\n'
printf '\nDo not rerun the complete 180-cell benchmark for the supervisor demo.\n'
