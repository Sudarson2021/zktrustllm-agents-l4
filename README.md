# ZKTrustLLM-Agents L4

Proof-governed agentic zero-trust control and reproducible evaluation for O-RAN edge security.

This repository contains artifact support for the ZKTrustLLM-Agents L4 journal manuscript. The goal is to make each major paper claim traceable to scripts, logs, hashes, generated tables, and explicit claim boundaries.

## Scope

ZKTrustLLM-Agents L4 evaluates governed autonomous O-RAN security workflows. It separates O-RAN governance, bounded telemetry/reasoning/policy/proof/audit agents, and evidence/trust/reproducibility functions.

The artifact focuses on reproducibility, policy gating, audit anchoring, negative-security rejection checks, and bounded AI-assisted workflow evaluation.

## Quick start

Run:

    bash scripts/reproduce_paper_258.sh

Outputs are written to:

    artifacts/out/paper_258/

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

## Main commands

- Paper-level validation wrapper: bash scripts/reproduce_paper_258.sh
- Core local reproduction: bash scripts/reproduce_all.sh
- Oracle-only baseline: bash scripts/baselines/run_oracle_only.sh
- No-IPFS baseline: bash scripts/baselines/run_no_ipfs.sh
- Packet-capture/direct telemetry smoke test: bash scripts/l4/media/run_packet_capture_smoke.sh
- AUTH_V2.x timing boundary check: bash scripts/l4/zk/collect_auth_v2_timing_guarded.sh
- Paper claim validation: python3 scripts/l4/validation/validate_paper_258_claims.py

## Claim boundary

This repository supports local scientific validation. It does not claim production-grade O-RAN deployment, Ethereum mainnet performance, semantic correctness of LLM reasoning, live media QoE unless a packet-capture experiment is explicitly run, or complete AUTH_V2.x prover timing unless direct timing logs exist for every reported row.

## API-key handling

For live AI evaluation, copy config/n8n/ai_eval.env.example to .env.ai_eval, fill keys locally, and source it. Never commit .env.ai_eval or raw logs containing provider credentials.

## Paper-to-code mapping

See ARTIFACTS.md.

## IEEE TNSM supervisor revision

The comment-by-comment revision package, manuscript-ready text, vector figure
replacements, updated standards references, submission materials, and empirical
completion gates are in
`docs/journal/tnsm_revision_20260808/`. New results must pass the supplied
baseline, injection, metadata, HTTP-failure, and human-label scripts before they
are inserted into the paper.

## Evidence classes

The artifact separates direct runtime evidence, public-testnet evidence, configured profile evidence, reproducibility evidence, and claim-boundary evidence. Configured media-profile values must not be reported as packet-capture measurements.
