# stage_ff_four_model_comm_n8n_final15

Generated: 2026-07-04T23:54:56
Total four-model communication records: 15
PASS/PARTIAL/FAIL: 15/0/0
Valid JSON all-steps: 15/15

| Scenario | Runs | Pass/Partial/Fail | Mean accuracy % | Mean agreement % | Mean latency ms | p95 latency ms | Mean configured cost USD |
|---|---:|---|---:|---:|---:|---:|---:|
| agent-collaboration | 3 | 3/0/0 | 100.0 | 100.0 | 31059.3 | 32865 | 0.06794774 |
| failure-recovery | 3 | 3/0/0 | 100.0 | 100.0 | 30578.7 | 29387 | 0.06947253 |
| model-disagreement-resolution | 3 | 3/0/0 | 100.0 | 100.0 | 29864.7 | 28056 | 0.06845889 |
| task-decomposition | 3 | 3/0/0 | 100.0 | 100.0 | 30301.7 | 27415 | 0.06948338 |
| verification-agent | 3 | 3/0/0 | 100.0 | 100.0 | 31781.0 | 33188 | 0.06937001 |

## Model communication chain

GPT-5.5 Planner -> Claude Fable 5 Evidence Critic -> DeepSeek Recovery Agent -> Mistral Verifier/Arbiter.

## Claim boundary

These Stage F/F results evaluate inter-AI model communication and orchestration behaviour around the local ZKTrustLLM-Agents L4 evidence artifact. They are not production O-RAN deployment validation, packet-capture network benchmarking, public-chain benchmarking, full media-plane QoE validation, or a 240-run six-variant ablation.
