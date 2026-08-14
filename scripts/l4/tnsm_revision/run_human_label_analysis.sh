#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 8B: analyze two completed independent annotation sheets.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
: "${COORDINATOR_KEY:?Set COORDINATOR_KEY to the Stage 8A oracle_key.csv path}"
: "${PREREGISTRATION:?Set PREREGISTRATION to the Stage 8A analysis_preregistration.json path}"
: "${ANNOTATOR_1_LABELS:?Set ANNOTATOR_1_LABELS to annotator 1 completed blinded_cases.csv}"
: "${ANNOTATOR_2_LABELS:?Set ANNOTATOR_2_LABELS to annotator 2 completed blinded_cases.csv}"
: "${ANNOTATOR_1_DECLARATION:?Set ANNOTATOR_1_DECLARATION to annotator 1 completed declaration CSV}"
: "${ANNOTATOR_2_DECLARATION:?Set ANNOTATOR_2_DECLARATION to annotator 2 completed declaration CSV}"
: "${EXPECTED_KEY_SHA256:?Set EXPECTED_KEY_SHA256 to the frozen Stage 8A oracle-key digest}"
: "${EXPECTED_PREREGISTRATION_SHA256:?Set EXPECTED_PREREGISTRATION_SHA256 to the frozen Stage 8A preregistration digest}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/human_label_analysis_$RUN_STAMP}"

for path in \
  "$COORDINATOR_KEY" \
  "$PREREGISTRATION" \
  "$ANNOTATOR_1_LABELS" \
  "$ANNOTATOR_2_LABELS" \
  "$ANNOTATOR_1_DECLARATION" \
  "$ANNOTATOR_2_DECLARATION"; do
  [[ -f "$path" ]] || {
    printf 'Required completed input not found: %s\n' "$path" >&2
    exit 2
  }
done
[[ ! -e "$OUTPUT_DIR" ]] || {
  printf 'Output directory already exists: %s\n' "$OUTPUT_DIR" >&2
  exit 2
}

python3 "$SCRIPT_DIR/analyze_human_labels.py" \
  --coordinator-key "$COORDINATOR_KEY" \
  --preregistration "$PREREGISTRATION" \
  --annotator-1 "$ANNOTATOR_1_LABELS" \
  --annotator-2 "$ANNOTATOR_2_LABELS" \
  --annotator-1-declaration "$ANNOTATOR_1_DECLARATION" \
  --annotator-2-declaration "$ANNOTATOR_2_DECLARATION" \
  --expected-key-sha256 "$EXPECTED_KEY_SHA256" \
  --expected-preregistration-sha256 "$EXPECTED_PREREGISTRATION_SHA256" \
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

ARCHIVE="$HOME/Downloads/tnsm_stage8b_human_label_analysis_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 8B human-label analysis completed. No provider call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
