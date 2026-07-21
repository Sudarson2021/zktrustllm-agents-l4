# ZKTrustLLM — Artifact & Prototype (Phase 1–5)

Prototype + artifacts for **ZKTrustLLM: IPFS-Anchored Zero-Knowledge Accountability for Secure 5G Edge Multicast**.

## Clarifications (addresses ICC reviewer concerns)
- IPFS is NOT used for live video streaming. IPFS stores audit evidence objects; the live media path remains DTLS/RTP/multicast.
- CID = Content Identifier (content-address for evidence in IPFS).
- ZK = Zero-Knowledge proof attesting properties about (score, evidence commitment, context) without revealing sensitive evidence.

## Reproduce / collect artifacts
Run:
  bash scripts/reproduce_all.sh

Outputs are collected under:
  artifacts/out/

## Baselines (comparisons)
Run:
  bash scripts/baselines/run_oracle_only.sh
  bash scripts/baselines/run_no_ipfs.sh

## Paper ↔ Code mapping
See:
  ARTIFACTS.md

## Scoring model
See:
  docs/scoring.md

## PoS versus genuine DPoS consensus-sensitivity study

The L4 extension includes a paired public-testnet experiment using identical
`Stage3AnomalyLedger` bytecode on Ethereum Sepolia (Ethereum PoS protocol;
permissioned test validator set) and IoTeX testnet (Roll-DPoS). The benchmark,
strict evidence gate, manuscript text, and reporting boundaries are documented in:

  docs/l4/consensus/POS_ROLLDPOS_EXPERIMENT.md

No consensus-comparison number is embedded in source code or claimed before the
measured multi-session evidence is available.
