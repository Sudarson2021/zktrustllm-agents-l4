#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 5: live three-case pilot first; the 30-case experiment is locked.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
MODE="${MODE:-pilot}"
MODEL_ID="${MODEL_ID:-gpt-5.6-terra}"
PINNED_SUITE_SHA256="0c884fb777897bcfe081f0bf8ed71bf005a06ec06bc25e69cb7cbc6e47464fb8"

case "$MODE" in
  pilot)
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/prompt_injection_gpt56terra_pilot}"
    RUN_LABEL="pilot"
    EXPECTED_SELECTED_CASES=3
    CASE_ARGS=(
      --case-id inj-01-01
      --case-id inj-02-04
      --case-id inj-03-09
    )
    ;;
  full)
    [[ "${CONFIRM_INJECTION_30:-}" == "YES" ]] || {
      printf 'The 30-case run is locked. Set CONFIRM_INJECTION_30=YES only after pilot acceptance.\n' >&2
      exit 2
    }
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/prompt_injection_gpt56terra_full_r1}"
    RUN_LABEL="full"
    EXPECTED_SELECTED_CASES=30
    CASE_ARGS=()
    ;;
  *)
    printf 'MODE must be pilot or full; received %s\n' "$MODE" >&2
    exit 2
    ;;
esac

[[ -n "${OPENAI_API_KEY:-}" ]] || {
  printf 'OPENAI_API_KEY is not set in this shell.\n' >&2
  exit 2
}

SUITE_TEMP="$(mktemp /tmp/zktrustllm-injection-suite.XXXXXX.jsonl)"
trap 'rm -f -- "$SUITE_TEMP"' EXIT
python3 "$SCRIPT_DIR/generate_prompt_injection_suite.py" --output "$SUITE_TEMP"
printf '%s  %s\n' "$PINNED_SUITE_SHA256" "$SUITE_TEMP" | sha256sum -c -

COMMON_ARGS=(
  --suite "$SUITE_TEMP"
  --output-dir "$OUTPUT_DIR"
  --expected-suite-sha256 "$PINNED_SUITE_SHA256"
  --expected-selected-cases "$EXPECTED_SELECTED_CASES"
  --endpoint https://api.openai.com
  --model "$MODEL_ID"
  --temperature 0
  --top-p 1
  --reasoning-effort none
  --max-completion-tokens 256
  --timeout 180
  --max-attempts 5
  --retry-base-delay 2
  --request-delay 0.25
  --input-price-per-mtok 2
  --output-price-per-mtok 12
  --pricing-snapshot-date 2026-08-08
)

python3 "$SCRIPT_DIR/run_prompt_injection_experiment.py" \
  "${COMMON_ARGS[@]}" "${CASE_ARGS[@]}"

if [[ "$MODE" == "full" ]]; then
  python3 "$SCRIPT_DIR/score_prompt_injection.py" \
    --suite "$OUTPUT_DIR/injection_suite_30.jsonl" \
    --results "$OUTPUT_DIR/records.jsonl" \
    --output "$OUTPUT_DIR/injection_score.json" \
    --expected-cases 30 \
    --require-pass
fi

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

RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$HOME/Downloads/tnsm_stage5_prompt_injection_${RUN_LABEL}_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 5 prompt-injection %s completed.\n' "$MODE"
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
