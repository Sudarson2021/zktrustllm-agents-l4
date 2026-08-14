#!/usr/bin/env bash
set -Eeuo pipefail

# Read-only Stage 9: scenario-clustered intervals and repeat consistency for Table V.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
N8N_ROOT="${N8N_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
EXPERIMENT_DIR="${EXPERIMENT_DIR:-$N8N_ROOT/runtime/experiments/l4_oracle_20260716T131803Z_r10}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/oracle_clustered_statistics_$RUN_STAMP}"

[[ -d "$N8N_ROOT" ]] || { printf 'n8n root not found: %s\n' "$N8N_ROOT" >&2; exit 2; }
[[ -d "$EXPERIMENT_DIR" ]] || { printf 'experiment not found: %s\n' "$EXPERIMENT_DIR" >&2; exit 2; }
[[ ! -e "$OUTPUT_DIR" ]] || { printf 'Output exists: %s\n' "$OUTPUT_DIR" >&2; exit 2; }

python3 "$SCRIPT_DIR/analyze_oracle_clustered.py" \
  --experiment-dir "$EXPERIMENT_DIR" \
  --n8n-root "$N8N_ROOT" \
  --output-dir "$OUTPUT_DIR"

{
  python3 --version
  uname -a
} > "$OUTPUT_DIR/runtime_versions.txt"

(
  cd "$OUTPUT_DIR"
  find . -type f ! -name SHA256SUMS.txt -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt
)

ARCHIVE_DIR="${ARCHIVE_DIR:-$HOME/Downloads}"
[[ -d "$ARCHIVE_DIR" ]] || { printf 'Archive directory not found: %s\n' "$ARCHIVE_DIR" >&2; exit 2; }
ARCHIVE="$ARCHIVE_DIR/tnsm_oracle_clustered_statistics_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nOracle clustered-statistics analysis complete. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
