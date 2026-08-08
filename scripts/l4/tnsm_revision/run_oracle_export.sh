#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 2: deterministic, provider-free export of the frozen R10 oracle.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
N8N_ROOT="${N8N_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
EXPERIMENT_DIR="${EXPERIMENT_DIR:-$N8N_ROOT/runtime/experiments/l4_oracle_20260716T131803Z_r10}"
EXPORT_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/oracle_export_$EXPORT_STAMP}"
CANONICAL_ORACLE="$OUTPUT_DIR/canonical_oracle_180.jsonl"

mkdir -p "$OUTPUT_DIR"

python3 "$SCRIPT_DIR/export_frozen_oracle.py" \
  --experiment-dir "$EXPERIMENT_DIR" \
  --n8n-root "$N8N_ROOT" \
  --output "$CANONICAL_ORACLE" \
  --manifest-output "$OUTPUT_DIR/export_manifest.json" \
  --probe-output "$OUTPUT_DIR/schema_probe.json"

python3 "$SCRIPT_DIR/preflight_experiments.py" \
  --repo-root "$REPO_ROOT" \
  --experiment-dir "$EXPERIMENT_DIR" \
  --n8n-root "$N8N_ROOT" \
  --oracle-jsonl "$CANONICAL_ORACLE" \
  --output-dir "$OUTPUT_DIR/preflight_validation"

(
  cd "$OUTPUT_DIR"
  sha256sum \
    canonical_oracle_180.jsonl \
    export_manifest.json \
    schema_probe.json \
    preflight_validation/preflight.json \
    preflight_validation/preflight.md \
    > SHA256SUMS.txt
)

ARCHIVE="$HOME/Downloads/tnsm_stage2_oracle_export_$EXPORT_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" \
  canonical_oracle_180.jsonl \
  export_manifest.json \
  schema_probe.json \
  preflight_validation \
  SHA256SUMS.txt

printf '\nStage 2 export complete. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
