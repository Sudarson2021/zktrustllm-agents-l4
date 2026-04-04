#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

IMAGE="${ZOKRATES_DOCKER_IMAGE:-zokrates/zokrates}"
LOG_DIR="logs/l4"
OUT_DIR="artifacts/out_l4/zokrates_docker"
mkdir -p "$LOG_DIR" "$OUT_DIR"

INPUT_JSON="artifacts/out_l4/zokrates_input.auth_v1.json"
ARGS_FILE="$OUT_DIR/auth_v1.flat_args.txt"

COMPILE_CMD_LOG="$LOG_DIR/zokrates_docker_compile_command.txt"
SETUP_CMD_LOG="$LOG_DIR/zokrates_docker_setup_command.txt"
WITNESS_CMD_LOG="$LOG_DIR/zokrates_docker_witness_command.txt"
PROOF_CMD_LOG="$LOG_DIR/zokrates_docker_proof_command.txt"
STATUS_LOG="$LOG_DIR/zokrates_docker_status.txt"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not installed or not in PATH" | tee "$STATUS_LOG"
  exit 1
fi

ensure_inputs() {
  if [ -f "$INPUT_JSON" ]; then
    return
  fi

  python3 scripts/l4/build_auth_v1_proof_payload.py
  python3 scripts/l4/build_auth_v1_circuit_input.py
  python3 scripts/l4/export_auth_v1_witness_inputs.py
  python3 scripts/l4/export_auth_v1_zokrates_inputs.py

  if [ ! -f "$INPUT_JSON" ]; then
    echo "Missing input file: $INPUT_JSON" | tee "$STATUS_LOG"
    exit 1
  fi
}

ensure_inputs

python3 - <<'PY'
import json
from pathlib import Path

inp = Path("artifacts/out_l4/zokrates_input.auth_v1.json")
out = Path("artifacts/out_l4/zokrates_docker/auth_v1.flat_args.txt")

with open(inp, "r") as f:
    data = json.load(f)

args = data["flatArguments"]
out.write_text(" ".join(args))
print(f"Wrote Docker flat args -> {out}")
print(f"Argument count -> {len(args)}")
PY

ARGS="$(cat "$ARGS_FILE")"

DOCKER_BASE=(docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$ROOT_DIR:/work" -w /work "$IMAGE" zokrates)

echo "${DOCKER_BASE[*]} compile -i circuits/auth_v1.zok -o artifacts/out_l4/zokrates_docker/auth_v1.out" > "$COMPILE_CMD_LOG"
echo "${DOCKER_BASE[*]} setup -i artifacts/out_l4/zokrates_docker/auth_v1.out --proving-scheme g16 -p artifacts/out_l4/zokrates_docker/proving.key -v artifacts/out_l4/zokrates_docker/verification.key" > "$SETUP_CMD_LOG"
echo "${DOCKER_BASE[*]} compute-witness -i artifacts/out_l4/zokrates_docker/auth_v1.out -o artifacts/out_l4/zokrates_docker/witness -a $ARGS" > "$WITNESS_CMD_LOG"
echo "${DOCKER_BASE[*]} generate-proof -i artifacts/out_l4/zokrates_docker/auth_v1.out -w artifacts/out_l4/zokrates_docker/witness -p artifacts/out_l4/zokrates_docker/proving.key -j artifacts/out_l4/zokrates_docker/proof.json" > "$PROOF_CMD_LOG"

echo "[ZoKrates Docker] image -> $IMAGE"

set +e
"${DOCKER_BASE[@]}" compile -i circuits/auth_v1.zok -o artifacts/out_l4/zokrates_docker/auth_v1.out | tee "$LOG_DIR/zokrates_docker_compile.out"
RC1=$?
set -e
if [ $RC1 -ne 0 ]; then
  echo "docker compile failed with exit code $RC1" | tee "$STATUS_LOG"
  exit $RC1
fi

if [ -f artifacts/out_l4/zokrates_docker/proving.key ] && [ -f artifacts/out_l4/zokrates_docker/verification.key ]; then
  echo "[ZoKrates Docker] existing proving/verification keys found; skipping setup" | tee "$STATUS_LOG"
else
  set +e
  "${DOCKER_BASE[@]}" setup -i artifacts/out_l4/zokrates_docker/auth_v1.out --proving-scheme g16 -p artifacts/out_l4/zokrates_docker/proving.key -v artifacts/out_l4/zokrates_docker/verification.key | tee "$LOG_DIR/zokrates_docker_setup.out"
  RC2=$?
  set -e
  if [ $RC2 -ne 0 ]; then
    echo "docker setup failed with exit code $RC2" | tee "$STATUS_LOG"
    exit $RC2
  fi
fi

set +e
"${DOCKER_BASE[@]}" compute-witness -i artifacts/out_l4/zokrates_docker/auth_v1.out -o artifacts/out_l4/zokrates_docker/witness -a $ARGS | tee "$LOG_DIR/zokrates_docker_witness.out"
RC3=$?
set -e
if [ $RC3 -ne 0 ]; then
  echo "docker compute-witness failed with exit code $RC3" | tee "$STATUS_LOG"
  exit $RC3
fi

set +e
"${DOCKER_BASE[@]}" generate-proof -i artifacts/out_l4/zokrates_docker/auth_v1.out -w artifacts/out_l4/zokrates_docker/witness -p artifacts/out_l4/zokrates_docker/proving.key -j artifacts/out_l4/zokrates_docker/proof.json | tee "$LOG_DIR/zokrates_docker_generate_proof.out"
RC4=$?
set -e
if [ $RC4 -ne 0 ]; then
  echo "docker generate-proof failed with exit code $RC4" | tee "$STATUS_LOG"
  exit $RC4
fi

echo "docker ZoKrates pipeline completed successfully" | tee -a "$STATUS_LOG"
echo "compiled output -> artifacts/out_l4/zokrates_docker/auth_v1.out"
echo "proving key     -> artifacts/out_l4/zokrates_docker/proving.key"
echo "verification key-> artifacts/out_l4/zokrates_docker/verification.key"
echo "witness file    -> artifacts/out_l4/zokrates_docker/witness"
echo "proof json      -> artifacts/out_l4/zokrates_docker/proof.json"
