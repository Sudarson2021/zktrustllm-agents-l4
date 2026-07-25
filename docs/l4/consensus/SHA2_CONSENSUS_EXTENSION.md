# Consensus and SHA-2 evidence-anchor extension

## What the supervisor comment means technically

The extension treats consensus and hashing as independent experimental factors:

- **Consensus** determines how a network orders and confirms an EVM transaction.
- **SHA-256 and SHA-512** are one-way hash functions that bind evidence. They are
  not encryption algorithms.

The measured public-testnet comparison remains:

1. Ethereum Sepolia: Gasper proof-of-stake protocol with a permissioned test
   validator set.
2. IoTeX testnet: Roll-DPoS with PBFT-style committee finalisation.

The manuscript visual also includes:

3. Raft: leader-based, majority-quorum, crash-fault-tolerant replicated log.
4. Besu QBFT: permissioned EVM consensus with Byzantine fault tolerance and a
   validator supermajority.

Raft and QBFT have no latency bars because this repository does not contain
measured multi-node evidence for them. Adding guessed or literature latency to
the public-testnet chart would be an invalid comparison.

## Hash comparison boundary

`HashCommitmentLedger.sol` supports:

- algorithm ID `1`: a complete 32-byte SHA-256 digest;
- algorithm ID `2`: a complete 64-byte SHA-512 digest; and
- a separate `computeSha256AndAnchor` entry point using Solidity's SHA-256
  built-in, which calls the EVM SHA-256 precompile.

The paired public-testnet benchmark uses `anchorDigest` for both algorithms.
Node.js computes both digests over the same retained payload before submission.
This makes the network result a comparison of digest width and anchoring cost,
not CPU hash throughput. The standard EVM has no SHA-512 precompile, so treating
SHA-512 as an equivalent on-chain built-in would be inaccurate.

## Tests

```bash
npm ci
npm run test:sha2-contract
npm run test:sha2-analysis
```

The contract tests cover both digest widths, the SHA-256 precompile path,
duplicate evidence IDs, zero IDs, invalid lengths, unknown algorithms, and
unauthorised submission.

The analysis tests cover the three-session gate, deterministic paper outputs,
wrong chain identity, insufficient sessions, and payload/digest tampering.

## Public-testnet collection

Create `.env` from `.env.example` and use funded test-only keys:

```dotenv
SEPOLIA_RPC_URL=https://your-sepolia-provider.example
SEPOLIA_PRIVATE_KEY=0x...
IOTEX_TESTNET_RPC_URL=https://babel-api.testnet.iotex.io
IOTEX_TESTNET_PRIVATE_KEY=0x...
```

Run three sessions from the same client host and RPC providers:

```bash
SESSION_ID=2026-07-25-sha2-session-1 REPEATS=30 WARMUPS=2 \
  PAYLOAD_BYTES=1024 npm run bench:sha2

SESSION_ID=2026-07-26-sha2-session-2 REPEATS=30 WARMUPS=2 \
  PAYLOAD_BYTES=1024 npm run bench:sha2

SESSION_ID=2026-07-27-sha2-session-3 REPEATS=30 WARMUPS=2 \
  PAYLOAD_BYTES=1024 npm run bench:sha2
```

Then derive the paper artifacts:

```bash
python3 scripts/l4/consensus/analyze_sha2_benchmark.py \
  --out paper/l4_conference/derived_consensus \
  runtime_artifacts/hash_consensus_comparison/2026-07-25-sha2-session-1/benchmark.json \
  runtime_artifacts/hash_consensus_comparison/2026-07-26-sha2-session-2/benchmark.json \
  runtime_artifacts/hash_consensus_comparison/2026-07-27-sha2-session-3/benchmark.json
```

The analyzer recomputes every SHA-256 and SHA-512 digest from the retained
payload, verifies chain identities, identical bytecode, receipts, events,
security probes, balanced algorithm order, fixed RPC origins, fixed payload
size, fixed Git commit, and fixed implementation hashes. It emits numerical
LaTeX only after all gates pass.

## Manuscript integration

- `figures/fig_consensus_protocols.tex`: protocol-flow comparison.
- `tables/table_sha2_semantics.tex`: exact SHA-2 properties and EVM paths.
- `figures/fig_sha2_paths.tex`: fair computation/anchoring boundary.
- `docs/journal/supervisor_consensus_sha2_extension.tex`: ready-to-paste
  journal section.
- `derived_consensus/*sha2*`: generated only from measured sessions.

## Reporting boundary

Report:

- “hash function,” not “encryption algorithm”;
- “precomputed full-digest anchoring,” not “on-chain SHA-512 hashing”;
- “first inclusion,” not “economic finality”;
- “Raft crash-fault tolerance,” not Byzantine tolerance; and
- “QBFT protocol-property comparison” until a real validator deployment is
  measured.
