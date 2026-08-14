#!/usr/bin/env bash
set -Eeuo pipefail

# Read-only audit of whether the historical 240-row matrix proves each row.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
MATRIX="${MATRIX:-$REPO_ROOT/docs/l4/supervisor_258/results/n8n_all_runs_240runs_duration.csv}"
CIRCUIT="${CIRCUIT:-$REPO_ROOT/circuits/auth_v2_2.zok}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/artifacts/out/tnsm_revision/zk_240_coverage_audit_$RUN_STAMP}"

[[ -f "$MATRIX" ]] || { printf 'Matrix not found: %s\n' "$MATRIX" >&2; exit 2; }
[[ -f "$CIRCUIT" ]] || { printf 'Circuit not found: %s\n' "$CIRCUIT" >&2; exit 2; }
[[ ! -e "$OUTPUT_DIR" ]] || { printf 'Output exists: %s\n' "$OUTPUT_DIR" >&2; exit 2; }

python3 "$SCRIPT_DIR/audit_zk_240_coverage.py" \
  --matrix "$MATRIX" \
  --circuit "$CIRCUIT" \
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
ARCHIVE="$ARCHIVE_DIR/tnsm_zk_240_coverage_audit_$RUN_STAMP.tar.gz"
tar -C "$OUTPUT_DIR" -czf "$ARCHIVE" .

printf '\nZK 240-row evidence audit complete. No provider or chain call was made.\n'
printf 'Output directory: %s\n' "$OUTPUT_DIR"
printf 'Upload archive: %s\n' "$ARCHIVE"
sha256sum "$ARCHIVE"
