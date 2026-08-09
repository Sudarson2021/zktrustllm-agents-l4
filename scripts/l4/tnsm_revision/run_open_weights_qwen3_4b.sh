#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 4: CPU-local Qwen3-4B pilot first; the 60-cell AGENTIC_RAG run is locked.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
MODE="${MODE:-pilot}"
MODEL_TAG="${MODEL_TAG:-qwen3:4b}"
OLLAMA_ENDPOINT="${OLLAMA_ENDPOINT:-http://127.0.0.1:11434}"
RETRIEVAL_MODE="AGENTIC_RAG"

case "$MODE" in
  pilot)
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/open_weights_qwen3_4b_pilot}"
    EXPECTED_SELECTED_ROWS=3
    CELL_ARGS=(
      --cell-id S1:AGENTIC_RAG:R01
      --cell-id S4:AGENTIC_RAG:R01
      --cell-id S6:AGENTIC_RAG:R01
    )
    ;;
  full)
    [[ "${CONFIRM_OPEN_WEIGHTS_60:-}" == "YES" ]] || {
      printf 'The 60-cell run is locked. Set CONFIRM_OPEN_WEIGHTS_60=YES only after pilot acceptance.\n' >&2
      exit 2
    }
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/open_weights_qwen3_4b_agentic_rag_r1}"
    EXPECTED_SELECTED_ROWS=60
    CELL_ARGS=()
    ;;
  *)
    printf 'MODE must be pilot or full; received %s\n' "$MODE" >&2
    exit 2
    ;;
esac

if [[ -z "${CANONICAL_ORACLE:-}" ]]; then
  ORACLE_SEARCH_ROOT="$REPO_ROOT/artifacts/out/tnsm_revision"
  [[ -d "$ORACLE_SEARCH_ROOT" ]] || {
    printf 'Oracle search directory does not exist: %s\n' "$ORACLE_SEARCH_ROOT" >&2
    exit 2
  }
  mapfile -t ORACLE_CANDIDATES < <(
    find "$ORACLE_SEARCH_ROOT" \
      -type f -name canonical_oracle_180.jsonl \
      -printf '%T@ %p\n' \
      | sort -nr
  )
  ((${#ORACLE_CANDIDATES[@]} > 0)) || {
    printf 'No canonical_oracle_180.jsonl was found.\n' >&2
    exit 2
  }
  CANONICAL_ORACLE="${ORACLE_CANDIDATES[0]#* }"
fi

command -v ollama >/dev/null 2>&1 || {
  printf 'Ollama is not installed or is absent from PATH.\n' >&2
  exit 2
}
command -v curl >/dev/null 2>&1 || {
  printf 'curl is required for the local readiness check.\n' >&2
  exit 2
}
curl --fail --silent --show-error --max-time 10 \
  "$OLLAMA_ENDPOINT/api/version" >/dev/null || {
    printf 'The local Ollama API is unavailable at %s. Start Ollama and retry.\n' \
      "$OLLAMA_ENDPOINT" >&2
    exit 2
  }
ollama show "$MODEL_TAG" >/dev/null 2>&1 || {
  printf 'Model %s is not installed. Run: ollama pull %s\n' "$MODEL_TAG" "$MODEL_TAG" >&2
  exit 2
}

COMMON_ARGS=(
  --input "$CANONICAL_ORACLE"
  --output-dir "$OUTPUT_DIR"
  --endpoint "$OLLAMA_ENDPOINT"
  --model "$MODEL_TAG"
  --retrieval-mode "$RETRIEVAL_MODE"
  --expected-selected-rows "$EXPECTED_SELECTED_ROWS"
  --expected-input-sha256 4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c
  --temperature 0
  --top-p 1
  --top-k 20
  --min-p 0
  --repeat-penalty 1
  --seed 20260808
  --max-completion-tokens 256
  --context-window 16384
  --num-thread 8
  --keep-alive 15m
  --timeout 900
  --metadata-timeout 60
  --max-attempts 3
  --retry-base-delay 2
  --request-delay 0.25
)

# The live invocation writes preflight.json before the first generation call.
# Keeping preflight and generation in one process ensures that a single Ollama
# model snapshot/configuration hash governs the complete evidence directory.
python3 "$SCRIPT_DIR/run_open_weights_baseline.py" \
  "${COMMON_ARGS[@]}" "${CELL_ARGS[@]}"

{
  python3 --version
  ollama --version
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
ARCHIVE="$HOME/Downloads/tnsm_stage4_open_weights_${MODE}_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 4 open-weights %s completed.\n' "$MODE"
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
