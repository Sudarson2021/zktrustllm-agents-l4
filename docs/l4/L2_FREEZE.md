# L2 Freeze Snapshot

Date: 2026-04-03
Branch: l4-zktrustllm-agents
Tag: l2-freeze-before-l4

## Preserved baseline
- Original three-plane ZKTrustLLM architecture
- DTLS/RTP media-path separation remains unchanged
- IPFS remains cold-path evidence storage only
- Trust-plane commitment-bound submission flow remains unchanged
- Existing submitFeedbackZK path preserved as L2 reference
- Existing trust aggregation and PolicyRegistry behavior preserved as L2 reference

## Baseline evidence collected
- artifacts/out/main/tenants_results.ndjson
- artifacts/out/baseline_oracle_only/results.ndjson
- artifacts/out/baseline_no_ipfs/tenants_results.ndjson
- artifacts/out/summary.txt

## Notes
- Linux npm optional dependency issue observed for fsevents; not treated as blocking.
- Wrapper scripts printed TODO messages, but reproduce_all.sh successfully generated baseline outputs.
- This document marks the frozen L2 reference before any L4 contract or agent changes.
