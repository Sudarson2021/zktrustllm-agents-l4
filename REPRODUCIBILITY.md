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
