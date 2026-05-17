#!/usr/bin/env bash
set -euo pipefail

echo "=== ZKTrustLLM Claim Boundary Check ==="

SEARCH_DIRS="docs README.md ARTIFACTS.md"

echo ""
echo "Checking for risky public-testnet claims..."
grep -RInE \
  "deployed to Sepolia|deployed on Sepolia|Polygon Amoy deployment completed|public testnet deployment completed|Etherscan verified|Polygonscan verified|public-chain validation completed" \
  $SEARCH_DIRS 2>/dev/null || true

echo ""
echo "Checking for risky frozen AuthV2.2 proof claims..."
grep -RInE \
  "frozen AuthV2\.2 proof payloads generated|completed AuthV2\.2 proof reproducibility|AuthV2\.2 proof\.frozen\.json exists|positive and negative AuthV2\.2 proof payloads generated" \
  $SEARCH_DIRS 2>/dev/null || true

echo ""
echo "Allowed boundary wording should say:"
echo "- local Hardhat validation only"
echo "- public testnet deployment is not claimed"
echo "- frozen AuthV2.2 proof payloads are not claimed yet"

echo ""
echo "Boundary check completed. Review any lines printed above."
