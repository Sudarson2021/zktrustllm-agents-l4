#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8765/run}"
RUNS_ROOT="runtime_artifacts/n8n/runs"
BATCH_FILE="runtime_artifacts/n8n/stage_d_latest_batch.txt"

mkdir -p "$RUNS_ROOT"

if [ "${RESUME:-0}" = "1" ] && [ -f "$BATCH_FILE" ]; then
  BATCH_ID="$(cat "$BATCH_FILE")"
else
  BATCH_ID="$(date +%Y%m%d_%H%M%S)"
  echo "$BATCH_ID" > "$BATCH_FILE"
fi

VARIANTS=("full-l4" "oracle-only" "no-ipfs")
PROFILES=("clean" "delay" "delay_jitter" "delay_jitter_loss")
REPEATS=(1 2 3 4 5 6 7 8 9 10)

echo "Stage D-real 120-run matrix"
echo "BASE_URL=$BASE_URL"
echo "RUNS_ROOT=$RUNS_ROOT"
echo "BATCH_ID=$BATCH_ID"
echo ""

total=0
done_count=0

for variant in "${VARIANTS[@]}"; do
  for profile in "${PROFILES[@]}"; do
    for repeat in "${REPEATS[@]}"; do
      total=$((total + 1))
      run_id="stage_d_${BATCH_ID}_${variant}_${profile}_r${repeat}"
      run_id="$(echo "$run_id" | sed 's/[^A-Za-z0-9_-]/_/g')"
      response_file="$RUNS_ROOT/${run_id}.response.json"
      manifest_file="$RUNS_ROOT/$run_id/manifest.json"

      if [ -f "$manifest_file" ]; then
        echo "[$total/120] SKIP existing manifest: $run_id"
        done_count=$((done_count + 1))
        continue
      fi

      echo "[$total/120] Running: variant=$variant profile=$profile repeat=$repeat run_id=$run_id"

      curl -sS --fail-with-body --max-time 1800 \
        -H "Content-Type: application/json" \
        -X POST "$BASE_URL" \
        -d "{\"variant\":\"$variant\",\"profile\":\"$profile\",\"repeat\":$repeat,\"run_id\":\"$run_id\",\"experiment_stage\":\"stage_d_real_120_matrix\"}" \
        -o "$response_file"

      python3 -m json.tool "$response_file" >/dev/null

      if [ ! -f "$manifest_file" ]; then
        echo "ERROR: missing manifest for $run_id" >&2
        exit 20
      fi

      echo "Manifest OK: $run_id"
      done_count=$((done_count + 1))
      echo "Completed so far: $done_count/120"
      echo "Sleeping 2 seconds..."
      sleep 2
      echo ""
    done
  done
done

echo "Stage D-real finished."
echo ""
echo "Manifest count for this batch:"
find "$RUNS_ROOT" -path "*stage_d_${BATCH_ID}_*/*manifest.json" -print | sort
find "$RUNS_ROOT" -path "*stage_d_${BATCH_ID}_*/*manifest.json" -print | wc -l
