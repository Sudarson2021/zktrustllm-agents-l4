#!/usr/bin/env bash
set -Eeuo pipefail

# Stage 3: three-cell pilot first; full 180-cell execution requires MODE=full.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
MODE="${MODE:-pilot}"
MODEL_ID="${MODEL_ID:-gpt-5.6-terra}"
VENV_DIR="${VENV_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/zktrustllm-tnsm-eval-venv}"

case "$MODE" in
  pilot)
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/langgraph_pilot_gpt56terra}"
    CELL_ARGS=(
      --cell-id S1:NO_RAG:R01
      --cell-id S2:RAG:R01
      --cell-id S4:AGENTIC_RAG:R01
    )
    ;;
  full)
    [[ "${CONFIRM_FULL_180:-}" == "YES" ]] || {
      printf 'Full execution is locked. Set CONFIRM_FULL_180=YES only after the pilot is accepted.\n' >&2
      exit 2
    }
    OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/langgraph_full_gpt56terra_r1}"
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

[[ -n "${OPENAI_API_KEY:-}" ]] || {
  printf 'OPENAI_API_KEY is not set in this shell.\n' >&2
  exit 2
}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install \
  --disable-pip-version-check \
  -r "$REPO_ROOT/requirements-tnsm-eval.txt"

COMMON_ARGS=(
  --input "$CANONICAL_ORACLE"
  --output-dir "$OUTPUT_DIR"
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
  --expected-input-sha256 4854f1d42d7824ae48ae3b37d8402d468c9f11034aa26b0fd9e96a21e1196c6c
  --input-price-per-mtok 2
  --output-price-per-mtok 12
  --pricing-snapshot-date 2026-08-08
)

"$VENV_DIR/bin/python" "$SCRIPT_DIR/run_langgraph_baseline.py" \
  "${COMMON_ARGS[@]}" "${CELL_ARGS[@]}" --preflight-only

"$VENV_DIR/bin/python" "$SCRIPT_DIR/run_langgraph_baseline.py" \
  "${COMMON_ARGS[@]}" "${CELL_ARGS[@]}"

"$VENV_DIR/bin/python" -m pip freeze > "$OUTPUT_DIR/python_packages_frozen.txt"

(
  cd "$OUTPUT_DIR"
  find . -type f ! -name SHA256SUMS.txt -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    > SHA256SUMS.txt
)

RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$HOME/Downloads/tnsm_stage3_langgraph_${MODE}_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nStage 3 %s completed.\n' "$MODE"
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
