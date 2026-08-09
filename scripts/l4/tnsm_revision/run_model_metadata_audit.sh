#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 7A: read-only inventory of model IDs, request metadata, prompts, and roles.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
EXPERIMENT_ID="l4_oracle_20260716T131803Z_r10"
N8N_ROOT="${N8N_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
EXPERIMENT_DIR="${EXPERIMENT_DIR:-$N8N_ROOT/runtime/experiments/$EXPERIMENT_ID}"
SOURCE_ROOT="${SOURCE_ROOT:-$N8N_ROOT}"
REVISION_ROOT="${REVISION_ROOT:-$REPO_ROOT/artifacts/out/tnsm_revision}"
STAGE_FF_JSONL="${STAGE_FF_JSONL:-$REPO_ROOT/docs/l4/supervisor_258/results/ai_eval_ff/stage_ff_four_model_comm_n8n_final15.jsonl}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REVISION_ROOT/model_metadata_audit_$RUN_STAMP}"

[[ -d "$N8N_ROOT" ]] || {
  printf 'N8N root not found: %s\n' "$N8N_ROOT" >&2
  exit 2
}
[[ -d "$EXPERIMENT_DIR" ]] || {
  printf 'Frozen R10 experiment not found: %s\n' "$EXPERIMENT_DIR" >&2
  exit 2
}
[[ -d "$SOURCE_ROOT" ]] || {
  printf 'Source root not found: %s\n' "$SOURCE_ROOT" >&2
  exit 2
}
[[ -f "$STAGE_FF_JSONL" ]] || {
  printf 'Stage F/F JSONL not found: %s\n' "$STAGE_FF_JSONL" >&2
  exit 2
}
[[ ! -e "$OUTPUT_DIR" ]] || {
  printf 'Output directory already exists: %s\n' "$OUTPUT_DIR" >&2
  exit 2
}

python3 "$SCRIPT_DIR/audit_model_metadata.py" \
  --experiment-dir "$EXPERIMENT_DIR" \
  --n8n-root "$N8N_ROOT" \
  --stage-ff-jsonl "$STAGE_FF_JSONL" \
  --source-root "$SOURCE_ROOT" \
  --revision-root "$REVISION_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --expected-successes 180 \
  --expected-provider-records 720

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

ARCHIVE="$HOME/Downloads/tnsm_stage7a_model_metadata_audit_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 7A model-metadata audit completed. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
