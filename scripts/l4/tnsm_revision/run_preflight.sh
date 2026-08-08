#!/usr/bin/env bash
set -Eeuo pipefail

# Read-only first gate for the IEEE TNSM follow-up experiments.
# No provider is contacted and no credential value is printed.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
EXPERIMENT_DIR="${EXPERIMENT_DIR:-$HOME/Downloads/deploy/n8n_l4_parallel/runtime/experiments/l4_oracle_20260716T131803Z_r10}"
N8N_ROOT="${N8N_ROOT:-$HOME/Downloads/deploy/n8n_l4_parallel}"
PREFLIGHT_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/preflight_$PREFLIGHT_STAMP}"

ARGS=(
  --repo-root "$REPO_ROOT"
  --experiment-dir "$EXPERIMENT_DIR"
  --n8n-root "$N8N_ROOT"
  --output-dir "$OUTPUT_DIR"
)

if [[ -n "${ORACLE_JSONL:-}" ]]; then
  ARGS+=(--oracle-jsonl "$ORACLE_JSONL")
fi

python3 "$SCRIPT_DIR/preflight_experiments.py" "${ARGS[@]}"

(
  cd "$OUTPUT_DIR"
  sha256sum preflight.json preflight.md > SHA256SUMS.txt
)

printf '\nPreflight complete. No model/provider call was made.\n'
printf 'Share these three files before the next experiment:\n'
printf '  %s\n' "$OUTPUT_DIR/preflight.json"
printf '  %s\n' "$OUTPUT_DIR/preflight.md"
printf '  %s\n' "$OUTPUT_DIR/SHA256SUMS.txt"
