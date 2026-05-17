#!/usr/bin/env bash
set -euo pipefail

OUT="artifacts/publication/submission_gate_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

echo "=== ZKTrustLLM-Agents L4 Journal Submission Gate ==="

git status > "$OUT/git_status.txt"
git branch --show-current > "$OUT/git_branch.txt"
git rev-parse HEAD > "$OUT/git_commit.txt"

npx hardhat compile > "$OUT/compile.log" 2>&1

npx hardhat test test/auth_v2_2_authz.test.js > "$OUT/auth_v2_2_authz.log" 2>&1

REPORT_GAS=true npx hardhat test test/auth_v2_2_authz.test.js > "$OUT/auth_v2_2_gas.log" 2>&1

bash scripts/ablations/run_ablations.sh > "$OUT/ablation_manifests.log" 2>&1

node scripts/publication/summarize_evidence.mjs > "$OUT/publication_summary.log" 2>&1

cp -r docs/journal "$OUT/docs_journal_snapshot" || true
cp artifacts/publication/EVIDENCE_SUMMARY.md "$OUT/EVIDENCE_SUMMARY.md" || true

cat > "$OUT/SUBMISSION_GATE_SUMMARY.md" <<MD
# ZKTrustLLM-Agents L4 Submission Gate Summary

Generated: $(date -Is)

## Completed checks

- Git status captured.
- Hardhat compile executed.
- AuthV2.2 authorization tests executed.
- AuthV2.2 gas report executed.
- Ablation manifests regenerated.
- Publication evidence summary regenerated.
- Manuscript replacement sections captured.

## Required before final journal submission

- Full Hardhat suite green.
- Frozen positive and negative AuthV2.2 proof payloads generated.
- End-to-end ablations executed, not only manifest generation.
- 20+ repeated local runs with confidence intervals.
- Public testnet validation only after funded RPC/private key setup.
MD

echo "Submission-gate evidence written to: $OUT"
