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

## Supervisor consensus and SHA-2 extension

The repository now separates consensus from evidence hashing and uses the
technically correct terminology: SHA-256 and SHA-512 are hash functions, not
encryption algorithms.

- `fig_consensus_protocols.tex` compares measured Ethereum Sepolia Gasper PoS
  and IoTeX Roll-DPoS/PBFT with sourced Raft (CFT) and QBFT (BFT) properties.
- `HashCommitmentLedger.sol` anchors complete 32-byte SHA-256 and 64-byte
  SHA-512 digests and exposes a separate EVM SHA-256 precompile path.
- `run_paired_sha2_benchmark.js` submits matched digests to Sepolia and IoTeX.
- `analyze_sha2_benchmark.py` requires three sessions, rehashes every retained
  payload, validates chain IDs/bytecode/receipts/events/probes, and generates
  the manuscript table and gas figure only after the evidence gate passes.

Run the offline verification:

```bash
npm run test:sha2-contract
npm run test:sha2-analysis
```

Run one funded public-testnet session:

```bash
REPEATS=30 WARMUPS=2 PAYLOAD_BYTES=1024 npm run bench:sha2
```

Do not add Raft, QBFT, or SHA-2 latency bars to the paper without raw measured
evidence. Raft is not Byzantine-fault tolerant, and the standard EVM provides a
SHA-256 precompile but no SHA-512 precompile.
