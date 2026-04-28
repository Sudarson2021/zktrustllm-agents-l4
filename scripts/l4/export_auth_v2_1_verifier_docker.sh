#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p contracts/l4/generated

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/work" \
  -w /work \
  zokrates/zokrates \
  zokrates export-verifier \
  -i artifacts/out_l4/zokrates_docker_auth_v2_1/verification.key \
  -o contracts/l4/generated/AuthV2_1Verifier.sol

echo "Verifier exported to contracts/l4/generated/AuthV2_1Verifier.sol"
