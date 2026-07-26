#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <unique-session-id>" >&2
  exit 2
fi

SESSION_ID="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "${REPO_ROOT}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Publication collection requires a clean Git worktree." >&2
  echo "Commit the reviewed implementation, then rerun this command." >&2
  exit 1
fi

SESSION_ID="${SESSION_ID}" \
REPEATS=30 \
WARMUPS=3 \
PROBE_INTERVAL_MS=1000 \
OUTPUT_ROOT="${COLLECTION_ROOT:-${REPO_ROOT}/evaluation_runs/permissioned-publication}" \
npm run bench:permissioned

echo
echo "Session completed. Verify before starting another session:"
echo "  cd evaluation_runs/permissioned-publication/${SESSION_ID}"
echo "  sha256sum --check SHA256SUMS.txt"
