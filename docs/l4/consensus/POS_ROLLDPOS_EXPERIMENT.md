# PoS versus Roll-DPoS consensus-sensitivity experiment

## Scientific scope

This experiment asks a deliberately bounded question:

> When the identical `Stage3AnomalyLedger` bytecode receives matched audit-anchor
> transactions at approximately the same time, how do client-observed first-inclusion
> latency, EVM execution gas, and observed block cadence differ between an Ethereum
> PoS-protocol testnet and a genuine delegated-proof-of-stake testnet?

It does **not** claim to benchmark consensus throughput, validator decentralization,
economic finality, mainnet cost, or the complete ZKTrustLLM-Agents/O-RAN pipeline.
The smart contract does not itself “implement PoS” or “implement DPoS”; consensus is
a property of the networks executing the same contract.

## Network selection

| Role | Network | Identity | Official basis |
|---|---|---:|---|
| PoS-protocol testnet | Ethereum Sepolia | chain ID `11155111` | Ethereum documents Sepolia as the application-development testnet and states that its validator set is permissioned and operated by client/testing teams. |
| DPoS testnet | IoTeX testnet | chain ID `4690` | IoTeX documents its consensus as Randomized Delegated Proof of Stake (Roll-DPoS), combining delegated validator election, VRF committee selection, and PBFT finalization. |

Primary sources:

- Ethereum network documentation: <https://ethereum.org/developers/docs/networks/>
- IoTeX Roll-DPoS documentation: <https://docs.iotex.io/blockchain/learn-iotex/core-concepts/consensus-mechanism>
- IoTeX testnet/EVM parameters: <https://docs.iotex.io/blockchain/learn-iotex/exchange-integration>
- IoTeX test-token instructions: <https://docs.iotex.io/blockchain/build/web3-development/get-testnet-iotx-tokens>

BNB Smart Chain is intentionally not used: its official consensus name is Proof of
Staked Authority (PoSA), so labelling a BSC comparison as pure DPoS would be
scientifically imprecise.

## Experimental protocol

1. Compile `Stage3AnomalyLedger` once with Solidity 0.8.20, optimizer 200 runs,
   and `viaIR=true`.
2. Verify both RPC chain IDs before spending any test token.
3. Deploy the identical creation bytecode to both testnets and verify that the
   deployed runtime-code Keccak-256 hashes match.
4. Execute three warm-up pairs; these are recorded but excluded from analysis.
5. Execute 30 measured pairs per session. Each pair uses the same commitment and
   evidence digest on both networks, and both transactions are submitted
   concurrently from the same client host.
6. Repeat the session at least three times in separate time windows, producing at
   least 90 matched transaction pairs overall. Do not change RPC providers,
   compiler settings, client host, or benchmark code between sessions.
7. After each session, collect at least 64 consecutive block headers from each
   network to estimate the block-interval distribution independently of the
   transaction sequence.
8. Run duplicate-commitment, zero-commitment, and unauthorized-submitter
   `eth_call` probes against each deployed contract. These are read-only execution
   probes, not mined reverting transactions.
9. Derive the paper table, figure, and results paragraph only with
   `analyze_pos_rolldpos.py`. Its default publication gate rejects fewer than three
   sessions, fewer than 30 measured pairs per session, wrong chain IDs, mismatched
   bytecode, incomplete receipts, missing events, or failed security probes.

## Metrics and estimands

The primary metric is client-observed time from submission API invocation to the
first successful receipt (`wait(1)`). It includes RPC/client overhead, propagation,
waiting for a producer, and prevailing public-testnet load. It is not economic
finality.

Secondary metrics are:

- RPC-acceptance latency;
- EVM gas used by `commit(bytes32,bytes32)`;
- deployment gas and first-inclusion latency;
- consecutive-block timestamp gaps;
- receipt/event integrity; and
- the three read-only rejection probes.

The analysis reports median, quartiles, P95, mean, sample standard deviation, and a
two-level hierarchical-bootstrap 95% confidence interval for medians. The bootstrap
resamples sessions and then matched pairs within sessions, using 10,000 replicates
and a fixed seed. The paired effect is IoTeX-minus-Sepolia latency and the
Sepolia-to-IoTeX latency ratio for each matched pair.

Gas prices are recorded for provenance only. Native-token fees are not compared
across ETH and IOTX because their units and economic values are not commensurable.

## Prerequisites

- A Sepolia RPC endpoint and funded test-only Sepolia account.
- A funded test-only IoTeX testnet account. The official IoTeX Developer Portal
  supplies test tokens.
- Node.js dependencies installed with `npm ci`.
- No private key committed to Git.

Populate `.env` from `.env.example`:

```dotenv
SEPOLIA_RPC_URL=https://your-sepolia-provider.example
SEPOLIA_PRIVATE_KEY=0x...
IOTEX_TESTNET_RPC_URL=https://babel-api.testnet.iotex.io
IOTEX_TESTNET_PRIVATE_KEY=0x...
```

Separate test-only keys are recommended. `DEPLOYER_PRIVATE_KEY` is supported as a
fallback for both networks but should never be a wallet holding real assets.

## Run and derive

Run one session at a time, choosing a unique identifier:

```bash
SESSION_ID=2026-07-21-session-1 REPEATS=30 WARMUPS=3 BLOCK_SAMPLE_SIZE=64 \
  npx hardhat run --config hardhat.consensus.config.js \
  scripts/l4/consensus/run_paired_pos_rolldpos_benchmark.js
```

The dedicated Hardhat configuration writes compiler output to
`.hardhat-consensus/`. This isolation is required because the repository contains
publication evidence under `artifacts/`; the consensus benchmark must not clean or
rewrite that evidence directory.

Repeat for `session-2` and `session-3`, then derive the manuscript artifacts:

```bash
python3 scripts/l4/consensus/analyze_pos_rolldpos.py \
  --out paper/l4_conference/derived_consensus \
  runtime_artifacts/consensus_comparison/2026-07-21-session-1/benchmark.json \
  runtime_artifacts/consensus_comparison/2026-07-21-session-2/benchmark.json \
  runtime_artifacts/consensus_comparison/2026-07-21-session-3/benchmark.json
```

Commit each session directory, its `SHA256SUMS.txt`, and the complete derived output.
The derivation manifest hashes every input and generated paper artifact.

## Required reporting boundary

Use the terms “Ethereum Sepolia (Ethereum PoS protocol; permissioned test validator
set)” and “IoTeX testnet (Roll-DPoS).” Report “first-inclusion latency,” not
“finality latency.” State that results are public-testnet observations under
prevailing load and from one client/RPC location. Do not generalize them to either
mainnet, overall consensus superiority, decentralization, or production O-RAN
performance.
