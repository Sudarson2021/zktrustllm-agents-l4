# Reproducibility Guide

Quick start:
  bash scripts/reproduce_all.sh

Outputs:
  artifacts/out/

Notes:
- IPFS is optional for running the collection script.
- Baseline wrappers are provided to support reviewer-requested comparisons.

Consensus-sensitivity extension:
- Protocol and claim boundaries: `docs/l4/consensus/POS_ROLLDPOS_EXPERIMENT.md`
- Paired benchmark: `scripts/l4/consensus/run_paired_pos_rolldpos_benchmark.js`
- Strict deterministic analysis: `scripts/l4/consensus/analyze_pos_rolldpos.py`
- The publication gate requires three sessions and 30 matched pairs per session.
- No PoS/Roll-DPoS numerical result is claimed until measured public-testnet
  evidence from both networks passes that gate.

Permissioned crash/non-participation extension:
- Protocol, setup, commands, and claim boundaries:
  `docs/l4/consensus/RAFT_QBFT_FAULT_EXPERIMENT.md`
- Real-cluster driver:
  `scripts/l4/consensus/permissioned/run_permissioned_fault_benchmark.js`
- Strict deterministic analysis:
  `scripts/l4/consensus/analyze_permissioned_faults.py`
- The publication gate requires three clean sessions and at least 30 retained
  observations per condition.
- Stopped QBFT validators measure crash/non-participation and quorum loss, not
  arbitrary Byzantine behavior.
