#!/usr/bin/env bash
set -euo pipefail

RUNS="${RUNS:-20}"
PIPELINE_CMD="${ZKTRUSTLLM_PIPELINE_CMD:-}"
OUT_DIR="artifacts/publication/repeated_runs_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUT_DIR"

if [ -z "$PIPELINE_CMD" ]; then
  echo "ERROR: Set ZKTRUSTLLM_PIPELINE_CMD first."
  echo "Example:"
  echo "  RUNS=20 ZKTRUSTLLM_PIPELINE_CMD='npm run l4:run' bash scripts/publication/run_20x_local_evidence.sh"
  cat package.json | jq '.scripts' || true
  exit 1
fi

echo "runs,command,start_time,end_time,status,duration_seconds" > "$OUT_DIR/run_summary.csv"

for i in $(seq 1 "$RUNS"); do
  run_dir="$OUT_DIR/run_$i"
  mkdir -p "$run_dir"

  start_iso="$(date -Is)"
  start_epoch="$(date +%s)"

  echo "=== Run $i/$RUNS ==="

  if bash -lc "$PIPELINE_CMD" > "$run_dir/stdout.log" 2> "$run_dir/stderr.log"; then
    status="PASS"
  else
    status="FAIL"
  fi

  end_iso="$(date -Is)"
  end_epoch="$(date +%s)"
  duration="$((end_epoch - start_epoch))"

  echo "$i,\"$PIPELINE_CMD\",$start_iso,$end_iso,$status,$duration" >> "$OUT_DIR/run_summary.csv"
done

python3 - <<PY
import csv, statistics, pathlib, json
out = pathlib.Path("$OUT_DIR")
rows = list(csv.DictReader(open(out/"run_summary.csv")))
durations = [float(r["duration_seconds"]) for r in rows]
passes = sum(1 for r in rows if r["status"] == "PASS")
n = len(rows)
summary = {
    "runs": n,
    "passes": passes,
    "pass_rate": passes / n if n else 0,
    "duration_mean_seconds": statistics.mean(durations) if durations else None,
    "duration_stdev_seconds": statistics.stdev(durations) if len(durations) > 1 else 0,
    "note": "This summary reports repeated local pipeline execution. Add KPI-specific parsers after confirming artifact filenames."
}
(out/"summary.json").write_text(json.dumps(summary, indent=2))
(out/"SUMMARY.md").write_text(
    "# 20-Run Local Evidence Summary\\n\\n"
    f"- Runs: {n}\\n"
    f"- Passes: {passes}\\n"
    f"- Pass rate: {summary['pass_rate']:.3f}\\n"
    f"- Mean duration seconds: {summary['duration_mean_seconds']}\\n"
    f"- Std duration seconds: {summary['duration_stdev_seconds']}\\n"
)
print(json.dumps(summary, indent=2))
PY

echo "Repeated-run evidence written to: $OUT_DIR"
