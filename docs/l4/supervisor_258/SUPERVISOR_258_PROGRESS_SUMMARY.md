# Supervisor 258 Progress Summary

## Completed

- Created branch `l4-supervisor-comments-258`.
- Added supervisor response matrix.
- Added KPI plan for journal-grade validation.
- Added TLA+ policy-gate formal model.
- Added n8n scientific novelty matrix.
- Added n8n-compatible evaluation runner.
- Added KPI aggregation and deduplication scripts.
- Added 24-run validation dataset.
- Added clean deduplicated 240-run duration dataset.
- Repaired stale RBAC baseline test to match the current `ReputationManager` ABI.
- Reran only the affected RBAC variant and refreshed the clean 240-run dataset.

## Current Scientific Evidence

The current dataset covers:

- 6 experimental variants,
- 4 impairment profiles,
- 10 repetitions per condition,
- 240 clean deduplicated records,
- pass/fail status,
- Git commit traceability,
- evidence hashes,
- wall-clock duration,
- Hardhat-derived gas and test KPIs where available.

## Current Limitation

The dataset currently supports reproducibility, duration, pass/fail, and smart-contract gas evidence. The next stage is to parse and populate deeper O-RAN and ZK KPIs such as prover time, anchor gas, RTP jitter, RTP loss, reasoning latency, replay rejection, and zero-anchor rejection.

## Paper Use

This evidence supports the claim that ZKTrustLLM-Agents L4 has been converted from a functional prototype into a reproducible scientific evaluation framework using n8n as an orchestration layer.
