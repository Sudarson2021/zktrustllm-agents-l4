#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 8A: build two blinded annotation packages and a separate oracle key.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
DEFAULT_ORACLE="$REPO_ROOT/artifacts/out/tnsm_revision/oracle_export_20260808T190951Z/canonical_oracle_180.jsonl"
ORACLE_JSONL="${ORACLE_JSONL:-$DEFAULT_ORACLE}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/human_label_package_$RUN_STAMP}"

[[ -f "$ORACLE_JSONL" ]] || {
  printf 'Canonical oracle not found: %s\n' "$ORACLE_JSONL" >&2
  printf 'Set ORACLE_JSONL to the Stage 2 canonical_oracle_180.jsonl path.\n' >&2
  exit 2
}
[[ ! -e "$OUTPUT_DIR" ]] || {
  printf 'Output directory already exists: %s\n' "$OUTPUT_DIR" >&2
  exit 2
}

python3 "$SCRIPT_DIR/make_human_label_subset.py" \
  --input "$ORACLE_JSONL" \
  --output-dir "$OUTPUT_DIR" \
  --size 30 \
  --seed 20260808

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

ANNOTATOR_1_ARCHIVE="$HOME/Downloads/tnsm_stage8a_annotator_1_$RUN_STAMP.tar.gz"
ANNOTATOR_2_ARCHIVE="$HOME/Downloads/tnsm_stage8a_annotator_2_$RUN_STAMP.tar.gz"
COORDINATOR_ARCHIVE="$HOME/Downloads/tnsm_stage8a_coordinator_DO_NOT_SHARE_$RUN_STAMP.tar.gz"
FULL_ARCHIVE="$HOME/Downloads/tnsm_stage8a_human_label_package_DO_NOT_SHARE_$RUN_STAMP.tar.gz"

tar -C "$OUTPUT_DIR/annotator_1" -czf "$ANNOTATOR_1_ARCHIVE" .
tar -C "$OUTPUT_DIR/annotator_2" -czf "$ANNOTATOR_2_ARCHIVE" .
tar -C "$OUTPUT_DIR/coordinator_DO_NOT_SHARE" -czf "$COORDINATOR_ARCHIVE" .
tar -C "$OUTPUT_DIR" -czf "$FULL_ARCHIVE" .

printf '\nStage 8A blinded human-label packages created. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf '\nSend only these separate packages after institutional ethics/data-protection confirmation:\n'
printf 'Annotator 1: %s\n' "$ANNOTATOR_1_ARCHIVE"
printf 'Annotator 2: %s\n' "$ANNOTATOR_2_ARCHIVE"
printf '\nNever send these coordinator packages to either annotator:\n'
printf 'Coordinator: %s\n' "$COORDINATOR_ARCHIVE"
printf 'Full validation archive: %s\n' "$FULL_ARCHIVE"
printf '\nSHA-256 digests:\n'
sha256sum \
  "$ANNOTATOR_1_ARCHIVE" \
  "$ANNOTATOR_2_ARCHIVE" \
  "$COORDINATOR_ARCHIVE" \
  "$FULL_ARCHIVE"
