#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 6: read-only diagnosis of the 53 frozen R10 HTTP-500 attempts.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
EXPERIMENT_ID="l4_oracle_20260716T131803Z_r10"
N8N_ROOT="${N8N_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
EXPERIMENT_DIR="${EXPERIMENT_DIR:-$N8N_ROOT/runtime/experiments/$EXPERIMENT_ID}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/http500_root_cause_$RUN_STAMP}"

[[ -d "$N8N_ROOT" ]] || {
  printf 'N8N root not found: %s\n' "$N8N_ROOT" >&2
  exit 2
}
[[ -d "$EXPERIMENT_DIR" ]] || {
  printf 'Frozen R10 experiment not found: %s\n' "$EXPERIMENT_DIR" >&2
  exit 2
}
[[ ! -e "$OUTPUT_DIR" ]] || {
  printf 'Output directory already exists: %s\n' "$OUTPUT_DIR" >&2
  exit 2
}

python3 "$SCRIPT_DIR/analyze_http_failures.py" \
  --experiment-dir "$EXPERIMENT_DIR" \
  --n8n-root "$N8N_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --expected-failures 53 \
  --expected-successes 180

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
)

ARCHIVE="$HOME/Downloads/tnsm_stage6_http500_root_cause_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 6 HTTP-500 analysis completed. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
