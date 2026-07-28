# Controlled etcd/Raft and Besu/QBFT fault experiment

## Scientific question

This extension replaces the earlier protocol-only Raft/QBFT labels with
controlled, reproducible local-cluster evidence. It asks:

1. Does a real three-member etcd/Raft cluster continue to commit writes after
   one follower stops and after a leader election?
2. Does it stop committing after majority loss and recover when quorum returns?
3. Does a real four-validator Hyperledger Besu/QBFT network continue to include
   `Stage3AnomalyLedger` transactions with 3/4 validators active?
4. Does block production stop with only 2/4 validators active and recover
   after quorum restoration plus an explicitly recorded operator-assisted
   restart of the three active validators?

The experiment does **not** send conflicting signed votes, forge messages,
corrupt state, or make a validator equivocate. Stopped QBFT processes therefore
measure crash/non-participation and quorum loss. They are not evidence of
arbitrary Byzantine-fault tolerance.

## Why Raft and QBFT latency are not ranked

The etcd path replicates key/value writes. The Besu path executes and includes
an EVM contract transaction. Their absolute latencies have different workload,
execution, batching, and block-period semantics. The analyzer reports changes
within each implementation and refuses a cross-family speed ranking.

## Pinned implementations

- etcd 3.5.17 (`etcd` and `etcdctl`), downloaded from the official etcd GitHub
  release and checked against the release `SHA256SUMS`.
- Hyperledger Besu 24.5.4, downloaded from the official Besu GitHub release.
  Its pinned archive SHA-256 is
  `2d2082bd2ebebdc24a45007dd3c9c45ea9b430ef8a4b6025be4ef3376317f5d7`;
  the installed launcher hash is embedded in every session.
- Solidity 0.8.20 through the repository's isolated
  `hardhat.consensus.config.js`.
- Ethers 6.15.0 `NonceManager` serializes the admin signer's transaction
  nonces. Every retained transaction is submitted sequentially and confirmed
  before the next transaction is sent.

Use the same pinned binaries, source commit, host, and settings for every
reported session.

## Linux prerequisites

Recommended minimum: Ubuntu 22.04/24.04, Java 17 or newer, Node.js 20 or newer,
Python 3.10 or newer, 8 GiB RAM, and free localhost ports:

- etcd client: 23790, 23800, 23810
- etcd peer: 23890, 23900, 23910
- Besu JSON-RPC: 8545--8548
- Besu P2P: 30303--30306

Install Ubuntu prerequisites:

```bash
sudo apt update
sudo apt install -y openjdk-17-jre-headless nodejs npm python3 curl tar
```

## One-time setup

```bash
git clone https://github.com/Sudarson2021/zktrustllm-agents-l4.git
cd zktrustllm-agents-l4
git switch agent/supervisor-sha-consensus-comparison

npm install
npm run install:permissioned
npm run test:permissioned-analysis
npx hardhat compile --config hardhat.consensus.config.js
```

Before collecting paper evidence, commit the reviewed experiment implementation
and confirm:

```bash
git status --short
git rev-parse HEAD
java -version
node --version
cat .tools/permissioned/VERSIONS.txt
```

`git status --short` must print nothing.

## Smoke run (never cite)

The smoke run validates process control and evidence structure with two retained
observations. It is deliberately marked non-publication:

```bash
SESSION_ID=smoke-$(date -u +%Y%m%dT%H%M%SZ) \
REPEATS=2 WARMUPS=0 PROBE_INTERVAL_MS=250 ALLOW_DIRTY=1 \
OUTPUT_ROOT="$PWD/evaluation_runs/permissioned-smoke" \
npm run bench:permissioned
```

Validate its evidence gate in smoke mode:

```bash
python3 scripts/l4/consensus/analyze_permissioned_faults.py \
  --allow-smoke --min-sessions 1 --min-observations 2 \
  --out evaluation_runs/permissioned-smoke/derived \
  evaluation_runs/permissioned-smoke/smoke-*/benchmark.json
```

Do not copy smoke values into the paper or `runtime_artifacts/`.

## Publication collection

Run three independent sessions from a clean, unchanged commit. Use separate
time windows and do not edit code, change Java/Node/Besu/etcd versions, or
change the host between sessions.

The publication wrapper applies a 120-second QBFT recovery observation
bound. After the deliberate 2/4 quorum-loss interval, QBFT round timeouts have
backed off exponentially. The harness restores quorum and performs the Besu-
documented operator-assisted restart of the three active validators, resetting
their round timers. The evidence records the recovery method, restarted
validator set, timeout reset, and measured recovery duration.

```bash
bash scripts/l4/consensus/permissioned/run_publication_session.sh \
  2026-07-28-permissioned-v3-session-1

bash scripts/l4/consensus/permissioned/run_publication_session.sh \
  2026-07-28-permissioned-v3-session-2

bash scripts/l4/consensus/permissioned/run_publication_session.sh \
  2026-07-28-permissioned-v3-session-3
```

Each session includes:

- 30 retained Raft writes per progress condition;
- 30 retained failed writes during Raft majority loss;
- one observed leader-election recovery event;
- 30 retained QBFT contract anchors per progress condition;
- 30 retained block-height probes with 2/4 QBFT validators active;
- one observed operator-assisted QBFT quorum-recovery event;
- duplicate, zero-commitment, and unauthorized-submitter rejection probes;
- excluded warm-ups, host/software metadata, source and executable hashes,
  raw process logs, and a `SHA256SUMS.txt` manifest.

## Evidence validation and paper artifacts

```bash
for session in evaluation_runs/permissioned-publication/*; do
  (
    cd "$session"
    sha256sum --check SHA256SUMS.txt
  )
done

python3 scripts/l4/consensus/analyze_permissioned_faults.py \
  --out paper/l4_conference/derived_consensus \
  evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-1/benchmark.json \
  evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-2/benchmark.json \
  evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-3/benchmark.json
```

The strict analyzer requires three distinct sessions, a single clean Git
commit, unchanged runner/analyzer/binary hashes, at least 30 observations per
cell, correct EVM receipts/events, recomputed payload commitments, complete
quorum-loss behavior, and passing contract rejection probes.

Generated files:

- `summary_permissioned_faults.json`
- `summary_permissioned_faults.csv`
- `results_permissioned_faults.tex`
- `table_permissioned_faults.tex`

Only after the strict analyzer succeeds, copy the raw sessions into the tracked
artifact tree:

```bash
mkdir -p runtime_artifacts/permissioned_faults
cp -a evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-1 \
  runtime_artifacts/permissioned_faults/
cp -a evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-2 \
  runtime_artifacts/permissioned_faults/
cp -a evaluation_runs/permissioned-publication/2026-07-28-permissioned-v3-session-3 \
  runtime_artifacts/permissioned_faults/
```

Collection stays under the ignored `evaluation_runs/` tree until validation so
that later sessions still observe a clean, unchanged Git worktree.

## Reviewer-facing claim boundary

Permitted claim:

> In controlled local deployments, three-member etcd/Raft and four-validator
> Besu/QBFT exhibited their expected crash/non-participation quorum boundaries,
> with operator-assisted recovery measured after quorum restoration and a
> documented validator restart that reset backed-off round timers.

Do not claim:

- arbitrary Byzantine attacks were measured;
- stopped validators exercised equivocation or forged-vote behavior;
- Raft is Byzantine-fault tolerant;
- etcd and EVM absolute latency values are directly comparable;
- local QBFT observations prove public-network or production O-RAN performance.
