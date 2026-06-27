#!/usr/bin/env bash
set -euo pipefail

OUT="artifacts/ablations"
mkdir -p "$OUT"

STAMP="$(date -Is)"
BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

make_variant () {
  NAME="$1"; DISABLED="$2"; FLAG="$3"; EXPECTED="$4"
  DIR="$OUT/$NAME"
  mkdir -p "$DIR"

  cat > "$DIR/variant.json" <<JSON
{
  "variant": "$NAME",
  "generated_at": "$STAMP",
  "branch": "$BRANCH",
  "commit": "$COMMIT",
  "disabled_component": "$DISABLED",
  "env_flag": "$FLAG",
  "status": "manifest_only_not_full_rerun",
  "expected_failure_mode": "$EXPECTED"
}
JSON
}

make_variant "no_policy_gate" \
  "Approval classification and policy gating" \
  "ZKTRUSTLLM_DISABLE_POLICY_GATE" \
  "Unsafe or ambiguous action boundary."

make_variant "no_audit_ledger" \
  "Hash-chained audit ledger" \
  "ZKTRUSTLLM_DISABLE_AUDIT_LEDGER" \
  "Evidence cannot be checked after execution."

make_variant "no_ipfs_anchor" \
  "IPFS cold-path anchoring" \
  "ZKTRUSTLLM_DISABLE_IPFS_ANCHOR" \
  "Evidence lacks CID lookup."

make_variant "no_onchain_registry" \
  "Smart-contract commitment registry" \
  "ZKTRUSTLLM_DISABLE_ONCHAIN_REGISTRY" \
  "No chain-verifiable anchor or replay check."

echo "Ablation manifests written to $OUT"
