#!/usr/bin/env bash
set -euo pipefail

VARIANT="${1:-full_l4}"
PROFILE="${2:-clean_baseline}"
REPEAT="${3:-1}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${VARIANT}_${PROFILE}_r${REPEAT}_${TIMESTAMP}"
OUT_DIR="$ROOT_DIR/artifacts/l4/n8n_runs/$RUN_ID"

mkdir -p "$OUT_DIR"

git -C "$ROOT_DIR" rev-parse HEAD > "$OUT_DIR/git_commit.txt"

cat > "$OUT_DIR/run_config.json" <<JSON
{
  "run_id": "$RUN_ID",
  "variant": "$VARIANT",
  "profile": "$PROFILE",
  "repeat": $REPEAT,
  "timestamp_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON

RAW_LOG="$OUT_DIR/raw.log"
HARDHAT_LOG="$OUT_DIR/hardhat_test.log"
STATUS="PASS"

{
  echo "===== ZKTrustLLM-Agents L4 n8n Evaluation Run ====="
  echo "run_id=$RUN_ID"
  echo "variant=$VARIANT"
  echo "profile=$PROFILE"
  echo "repeat=$REPEAT"
  echo "git_commit=$(cat "$OUT_DIR/git_commit.txt")"
  echo

  case "$VARIANT" in
    full_l4)
      echo "[variant] full_l4"
      if [ -f "$ROOT_DIR/scripts/reproduce_all.sh" ]; then
        bash "$ROOT_DIR/scripts/reproduce_all.sh" || STATUS="FAIL"
      else
        echo "[warn] scripts/reproduce_all.sh not found"
      fi
      ;;

    oracle_only)
      echo "[variant] oracle_only"
      if [ -f "$ROOT_DIR/scripts/baselines/run_oracle_only.sh" ]; then
        bash "$ROOT_DIR/scripts/baselines/run_oracle_only.sh" || STATUS="FAIL"
      else
        echo "[warn] oracle-only baseline script not found"
      fi
      ;;

    no_ipfs)
      echo "[variant] no_ipfs"
      if [ -f "$ROOT_DIR/scripts/baselines/run_no_ipfs.sh" ]; then
        bash "$ROOT_DIR/scripts/baselines/run_no_ipfs.sh" || STATUS="FAIL"
      else
        echo "[warn] no-IPFS baseline script not found"
      fi
      ;;

    rbac_only)
      echo "[variant] rbac_only"
      cd "$ROOT_DIR"
      npx hardhat test || STATUS="FAIL"
      ;;

    no_zk)
      echo "[variant] no_zk"
      echo "[todo] connect to no-ZK ablation script when implemented"
      ;;

    no_policy_gate)
      echo "[variant] no_policy_gate"
      echo "[safety] simulated only; unsafe actions must never execute"
      ;;

    *)
      echo "[error] unknown variant: $VARIANT"
      STATUS="FAIL"
      ;;
  esac
} > "$RAW_LOG" 2>&1 || STATUS="FAIL"

if [ -f "$ROOT_DIR/package.json" ]; then
  (cd "$ROOT_DIR" && npx hardhat test > "$HARDHAT_LOG" 2>&1) || true
fi

sha256sum "$RAW_LOG" > "$OUT_DIR/evidence.sha256"

cat > "$OUT_DIR/kpis.json" <<JSON
{
  "run_id": "$RUN_ID",
  "variant": "$VARIANT",
  "profile": "$PROFILE",
  "repeat": $REPEAT,
  "status": "$STATUS",
  "git_commit": "$(cat "$OUT_DIR/git_commit.txt")",
  "raw_log": "$RAW_LOG",
  "hardhat_log": "$HARDHAT_LOG",
  "evidence_sha256": "$(cut -d ' ' -f1 "$OUT_DIR/evidence.sha256")",
  "reason_latency_ms": null,
  "a2a_reference_bytes": null,
  "prover_time_ms": null,
  "verifier_gas": null,
  "anchor_gas": null,
  "rtp_jitter_ms": null,
  "rtp_loss_pct": null,
  "dtls_rtp_jitter_ms": null,
  "dtls_rtp_loss_pct": null,
  "replay_rejected": null,
  "zero_anchor_rejected": null,
  "unauthorized_submitter_rejected": null
}
JSON

echo "$OUT_DIR/kpis.json"
