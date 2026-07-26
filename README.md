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
- `table_consensus_families.tex` states the fault model, commit pattern, and
  measured/reference status for all four protocols.
- `HashCommitmentLedger.sol` anchors complete 32-byte SHA-256 and 64-byte
  SHA-512 digests and exposes a separate EVM SHA-256 precompile path.
- `HashPrimitiveMicrobenchmark.sol` provides a local-only Keccak-256,
  SHA-256, and pure-Solidity SHA-512 comparison, gated by standard vectors.
- `run_paired_sha2_benchmark.js` submits matched digests to Sepolia and IoTeX.
- `analyze_sha2_benchmark.py` requires three sessions, rehashes every retained
  payload, validates chain IDs/bytecode/receipts/events/probes, and generates
  the manuscript table and gas figure only after the evidence gate passes.

Run the offline verification:

```bash
npm run test:sha2-contract
npm run test:sha2-analysis
npm run test:hash-local-contract
npm run test:hash-local-analysis
npm run test:permissioned-analysis
```

Run the real local-cluster smoke (never cite smoke values) and follow the
three-session publication protocol in:

- `docs/l4/consensus/RAFT_QBFT_FAULT_EXPERIMENT.md`
- `scripts/l4/consensus/permissioned/run_permissioned_fault_benchmark.js`
- `scripts/l4/consensus/analyze_permissioned_faults.py`

The permissioned extension starts three real etcd/Raft members and four real
Besu/QBFT validators. It measures process crash/non-participation, quorum loss,
and recovery. It does not inject equivocation or arbitrary Byzantine messages,
and it does not rank absolute etcd and EVM latencies.

Generate the separately labelled local primitive figure:

```bash
SESSION_ID=local-hash-$(date -u +%Y%m%dT%H%M%SZ) \
  REPEATS=30 WARMUPS=3 PAYLOAD_BYTES=32,1024 npm run bench:hash-local

python3 scripts/l4/consensus/analyze_hash_microbenchmark.py \
  --out paper/l4_conference/derived_consensus \
  runtime_artifacts/hash_microbenchmark/<SESSION_ID>/benchmark.json
```

Run one funded public-testnet session:

```bash
REPEATS=30 WARMUPS=2 PAYLOAD_BYTES=1024 npm run bench:sha2
```

Fig. 6 remains exclusively the measured 90-pair Sepolia/IoTeX latency result.
Do not add Raft, QBFT, or SHA-2 latency bars without raw deployment evidence
that passes its experiment-specific gate.
Raft is not Byzantine-fault tolerant, and the standard EVM provides a SHA-256
precompile but no SHA-512 precompile. The local SHA-512 bar is explicitly a
pure-Solidity reference; deployment computes SHA-512 off chain and anchors the
full 64-byte digest.
