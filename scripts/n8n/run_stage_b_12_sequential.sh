#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8765/run}"
RUNS_ROOT="runtime_artifacts/n8n/runs"
BATCH_ID="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$RUNS_ROOT"

VARIANTS=("full-l4" "oracle-only" "no-ipfs")
REPEATS=(1 2 3 4)

echo "Stage B sequential run"
echo "BASE_URL=$BASE_URL"
echo "RUNS_ROOT=$RUNS_ROOT"
echo "BATCH_ID=$BATCH_ID"
echo "$BATCH_ID" > runtime_artifacts/n8n/stage_b_latest_batch.txt
echo ""

for variant in "${VARIANTS[@]}"; do
  for repeat in "${REPEATS[@]}"; do
    run_id="stage_b_${BATCH_ID}_${variant}_clean_r${repeat}"
    run_id="$(echo "$run_id" | sed 's/[^A-Za-z0-9_-]/_/g')"
    response_file="$RUNS_ROOT/${run_id}.response.json"

    echo "Running: variant=$variant repeat=$repeat run_id=$run_id"

    curl -sS --fail-with-body --max-time 1200 \
      -H "Content-Type: application/json" \
      -X POST "$BASE_URL" \
      -d "{\"variant\":\"$variant\",\"profile\":\"clean\",\"repeat\":$repeat,\"run_id\":\"$run_id\",\"experiment_stage\":\"stage_b_repeatability\"}" \
      -o "$response_file"

    python3 -m json.tool "$response_file" >/dev/null

    if [ ! -f "$RUNS_ROOT/$run_id/manifest.json" ]; then
      echo "ERROR: missing manifest for $run_id" >&2
      exit 20
    fi

    echo "Manifest OK: $run_id"
    echo "Sleeping 3 seconds to avoid shared-state overlap..."
    sleep 3
    echo ""
  done
done

echo "Stage B sequential run finished."
echo ""
echo "Manifest count for this batch:"
find "$RUNS_ROOT" -path "*stage_b_${BATCH_ID}_*/*manifest.json" -print | sort
find "$RUNS_ROOT" -path "*stage_b_${BATCH_ID}_*/*manifest.json" -print | wc -l
