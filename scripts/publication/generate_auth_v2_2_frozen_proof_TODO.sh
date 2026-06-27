#!/usr/bin/env bash
set -euo pipefail

OUT="runtime_artifacts/l4/auth_v2_2"
mkdir -p "$OUT"

echo "AuthV2.2 frozen proof generation TODO"
echo "===================================="
echo ""
echo "This script is a placeholder until the exact ZoKrates AuthV2.2 circuit input vector is confirmed."
echo ""
echo "Expected public inputs for AuthV2.2:"
echo "[agentKey, capabilityIdHi, capabilityIdLo, policyClassHash, actionClass, expiryBucket, contextHash, policyAdmissibilityFlag, trustState]"
echo ""
echo "Before final submission, generate:"
echo "  $OUT/proof.frozen.json"
echo "  $OUT/proof.bad.json"
echo "  $OUT/proof_payload.auth_v2_2.frozen.json"
echo ""
echo "Discovery files:"
echo "  artifacts/journal_hardening/zk_discovery/auth_v2_1_flow.txt"
echo "  artifacts/journal_hardening/zk_discovery/auth_v2_2_flow.txt"
echo ""
echo "Do not claim frozen AuthV2.2 proof evidence until those files exist."

exit 1
