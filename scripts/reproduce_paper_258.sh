#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/artifacts/out/paper_258"
LOG="$OUT/logs"

mkdir -p "$OUT" "$LOG"

echo "[paper-258] root: $ROOT"
echo "[paper-258] output: $OUT"

git -C "$ROOT" rev-parse HEAD > "$OUT/git_commit.txt"
git -C "$ROOT" status --short > "$OUT/git_status_short.txt" || true

run_step() {
  local name="$1"
  shift

  echo ""
  echo "===== $name ====="

  set +e
  "$@" >"$LOG/${name}.stdout.log" 2>"$LOG/${name}.stderr.log"
  local rc=$?
  set -e

  echo "$rc" > "$LOG/${name}.exit_code"

  if [ "$rc" -eq 0 ]; then
    echo "[OK] $name"
  else
    echo "[WARN] $name failed or skipped; see $LOG/${name}.stderr.log"
  fi
}

if [ -x "$ROOT/scripts/reproduce_all.sh" ]; then
  run_step core_reproduce_all bash "$ROOT/scripts/reproduce_all.sh"
else
  echo "MISSING scripts/reproduce_all.sh" > "$LOG/core_reproduce_all.stderr.log"
  echo "127" > "$LOG/core_reproduce_all.exit_code"
fi

if [ -x "$ROOT/scripts/l4/media/run_packet_capture_smoke.sh" ]; then
  run_step media_packet_capture bash "$ROOT/scripts/l4/media/run_packet_capture_smoke.sh"
else
  echo "MISSING packet-capture script" > "$LOG/media_packet_capture.stderr.log"
  echo "127" > "$LOG/media_packet_capture.exit_code"
fi

if [ -x "$ROOT/scripts/l4/zk/collect_auth_v2_timing_guarded.sh" ]; then
  run_step auth_v2_timing bash "$ROOT/scripts/l4/zk/collect_auth_v2_timing_guarded.sh"
run_step auth_v2_analysis python3 "$ROOT/scripts/l4/validation/analyze_auth_v2_timing.py"
else
  echo "MISSING AUTH_V2 timing script" > "$LOG/auth_v2_timing.stderr.log"
  echo "127" > "$LOG/auth_v2_timing.exit_code"
fi

if [ -f "$ROOT/runtime_artifacts/n8n/model_tool_scenarios/records.jsonl" ] && [ -f "$ROOT/scripts/l4/metrics/build_n8n_model_tool_tables.py" ]; then
  run_step ai_table_builder python3 "$ROOT/scripts/l4/metrics/build_n8n_model_tool_tables.py" \
    --input "$ROOT/runtime_artifacts/n8n/model_tool_scenarios/records.jsonl" \
    --out-dir "$OUT/ai_eval" \
    --paper-table "$OUT/table_multimodel_tool_scenarios.tex"
else
  echo "SKIPPED: no live AI records found at runtime_artifacts/n8n/model_tool_scenarios/records.jsonl" > "$LOG/ai_table_builder.stderr.log"
  echo "0" > "$LOG/ai_table_builder.exit_code"
fi


# Normalize Stage E/F final-90 records into the canonical path if available.
EXPECTED_AI_RECORDS="$ROOT/runtime_artifacts/n8n/model_tool_scenarios/records.jsonl"
if [ ! -f "$EXPECTED_AI_RECORDS" ]; then
  mkdir -p "$(dirname "$EXPECTED_AI_RECORDS")"

  for CANDIDATE in \
    "$ROOT/runtime_artifacts/n8n/model_tool_scenarios_final_90_v2/records.jsonl" \
    "$ROOT/docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_final90.jsonl" \
    "$ROOT/docs/l4/supervisor_258/results/ai_eval/stage_ef_three_model_n8n_final90.jsonl"
  do
    if [ -f "$CANDIDATE" ]; then
      cp "$CANDIDATE" "$EXPECTED_AI_RECORDS"
      echo "[paper-258] normalized Stage E/F records from $CANDIDATE"
      break
    fi
  done
fi

run_step media_packet_capture_final bash "$ROOT/scripts/l4/media/run_packet_capture_smoke.sh"
run_step ai_evidence_summary python3 "$ROOT/scripts/l4/validation/summarize_ai_evidence.py"
run_step stage_ef_failure_analysis python3 "$ROOT/scripts/l4/validation/analyze_stage_ef_failures.py"
run_step stage_ff_row_hashes python3 "$ROOT/scripts/l4/validation/hash_stage_ff_rows.py"
run_step claim_validation python3 "$ROOT/scripts/l4/validation/validate_paper_258_claims.py"
run_step evidence_manifest python3 "$ROOT/scripts/l4/validation/build_evidence_manifest.py"
run_step claim_validation_final python3 "$ROOT/scripts/l4/validation/validate_paper_258_claims.py"
run_step evidence_manifest_final python3 "$ROOT/scripts/l4/validation/build_evidence_manifest.py"

echo ""
echo "[DONE] Paper-258 validation outputs under $OUT"
