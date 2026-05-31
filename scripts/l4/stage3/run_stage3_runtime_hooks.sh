#!/usr/bin/env bash
set -euo pipefail

VARIANT="${1:-full_l4}"
PROFILE="${2:-clean_baseline}"
REPEAT="${3:-1}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$ROOT_DIR"

echo "===== Stage 3 Direct Runtime Hooks ====="
echo "variant=$VARIANT"
echo "profile=$PROFILE"
echo "repeat=$REPEAT"

python3 scripts/l4/stage3/run_reasoning_probe.py \
  --variant "$VARIANT" \
  --profile "$PROFILE" \
  --repeat "$REPEAT"

npx hardhat test test/l4/stage3_runtime_hooks.test.js
