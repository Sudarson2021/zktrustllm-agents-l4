# stage_e_claude_fable5_single_pilot

Generated: 2026-07-04T15:23:54
Total measured records: 3

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 1 | 1/0/0 | 100.0 | 100.0 | 5735.0 | 5735 | 0.01452000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 1 | 1/0/0 | 100.0 | 100.0 | 5114.0 | 5114 | 0.01053000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 1 | 1/0/0 | 100.0 | 100.0 | 6346.0 | 6346 | 0.02216000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
