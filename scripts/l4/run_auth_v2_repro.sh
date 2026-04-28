#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

mkdir -p logs/l4
mkdir -p artifacts/out_l4/zokrates_docker_auth_v2
mkdir -p contracts/l4/generated

echo "[AUTH_V2] build payload"
python3 scripts/l4/build_auth_v2_proof_payload.py | tee logs/l4/auth_v2_build_payload.out
cp artifacts/out_l4/proof_payload.auth_v2.json artifacts/out_l4/proof_payload.auth_v2.frozen.json


echo "[AUTH_V2] build circuit input"
python3 scripts/l4/build_auth_v2_circuit_input.py | tee logs/l4/auth_v2_build_circuit_input.out

echo "[AUTH_V2] export ZoKrates inputs"
python3 scripts/l4/export_auth_v2_zokrates_inputs.py | tee logs/l4/auth_v2_export_inputs.out

echo "[AUTH_V2] compile circuit"
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/work" \
  -w /work \
  zokrates/zokrates \
  zokrates compile \
  -i circuits/auth_v2.zok \
  -o artifacts/out_l4/zokrates_docker_auth_v2/auth_v2.out | tee logs/l4/auth_v2_compile.out

echo "[AUTH_V2] setup"
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/work" \
  -w /work \
  zokrates/zokrates \
  zokrates setup \
  -i artifacts/out_l4/zokrates_docker_auth_v2/auth_v2.out \
  -p artifacts/out_l4/zokrates_docker_auth_v2/proving.key \
  -v artifacts/out_l4/zokrates_docker_auth_v2/verification.key | tee logs/l4/auth_v2_setup.out

echo "[AUTH_V2] compute witness"
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/work" \
  -w /work \
  zokrates/zokrates \
  zokrates compute-witness \
  -i artifacts/out_l4/zokrates_docker_auth_v2/auth_v2.out \
  -o artifacts/out_l4/zokrates_docker_auth_v2/witness \
  -a $(cat artifacts/out_l4/auth_v2.flat_args.txt) | tee logs/l4/auth_v2_witness.out

echo "[AUTH_V2] generate proof"
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$PWD:/work" \
  -w /work \
  zokrates/zokrates \
  zokrates generate-proof \
  -i artifacts/out_l4/zokrates_docker_auth_v2/auth_v2.out \
  -w artifacts/out_l4/zokrates_docker_auth_v2/witness \
  -p artifacts/out_l4/zokrates_docker_auth_v2/proving.key \
  -j artifacts/out_l4/zokrates_docker_auth_v2/proof.json | tee logs/l4/auth_v2_generate_proof.out

cp artifacts/out_l4/zokrates_docker_auth_v2/proof.json artifacts/out_l4/zokrates_docker_auth_v2/proof.frozen.json


echo "[AUTH_V2] export verifier"
bash scripts/l4/export_auth_v2_verifier_docker.sh | tee logs/l4/auth_v2_export_verifier.out

echo "[AUTH_V2] hardhat compile"
npx hardhat compile | tee logs/l4/auth_v2_hardhat_compile.out

echo "[AUTH_V2] deploy wrapper"
npx hardhat run scripts/l4/deploy_auth_v2_wrapper.js --network localhost | tee logs/l4/auth_v2_deploy_wrapper.out

echo "[AUTH_V2] direct verifier check"
python3 scripts/l4/check_auth_v2_groth16_verifier.py | tee logs/l4/auth_v2_check_verifier.out

echo "[AUTH_V2] wrapper check"
python3 scripts/l4/check_auth_v2_wrapper.py | tee logs/l4/auth_v2_check_wrapper.out

echo "[AUTH_V2] positive submit"
python3 scripts/l4/direct_submit_auth_v2.py | tee logs/l4/auth_v2_submit_positive.out

echo "[AUTH_V2] build bad proof"
python3 scripts/l4/build_auth_v2_bad_groth16_proof.py | tee logs/l4/auth_v2_build_bad_proof.out

echo "[AUTH_V2] negative verifier check"
python3 scripts/l4/check_auth_v2_groth16_verifier_bad.py | tee logs/l4/auth_v2_check_verifier_bad.out

echo "[AUTH_V2] negative wrapper check"
python3 scripts/l4/check_auth_v2_wrapper_bad.py | tee logs/l4/auth_v2_check_wrapper_bad.out

echo "[AUTH_V2] negative submit"
python3 scripts/l4/direct_submit_auth_v2_bad.py | tee logs/l4/auth_v2_submit_bad.out

echo
echo "=== AUTH_V2 REPRO SUMMARY ==="
echo "Proof file      : artifacts/out_l4/zokrates_docker_auth_v2/proof.json"
echo "Bad proof file  : artifacts/out_l4/zokrates_docker_auth_v2/proof.bad.json"
echo "Verifier export : contracts/l4/generated/AuthV2Verifier.sol"
echo "Deployments     : deployments/l4.localhost.json"
echo "Logs            : logs/l4/auth_v2_*"
