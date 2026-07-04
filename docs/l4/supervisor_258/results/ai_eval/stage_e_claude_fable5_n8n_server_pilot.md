# stage_e_claude_fable5_n8n_server_pilot

Generated: 2026-07-04T15:26:31
Total measured records: 3

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 1 | 1/0/0 | 100.0 | 100.0 | 7681.0 | 7681 | 0.01257000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 1 | 1/0/0 | 100.0 | 100.0 | 4414.0 | 4414 | 0.01068000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 1 | 1/0/0 | 100.0 | 100.0 | 6638.0 | 6638 | 0.02176000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
