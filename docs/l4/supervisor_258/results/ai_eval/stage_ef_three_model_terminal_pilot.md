# stage_ef_three_model_terminal_pilot

Generated: 2026-07-04T15:33:02
Total measured records: 24

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 1 | 1/0/0 | 100.0 | 100.0 | 5837.0 | 5837 | 0.01272000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 1 | 1/0/0 | 100.0 | 100.0 | 4483.0 | 4483 | 0.01053000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 1 | 1/0/0 | 100.0 | 100.0 | 6487.0 | 6487 | 0.02076000 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | claim-boundary-review | 1 | 1/0/0 | 100.0 | 100.0 | 1482.0 | 1482 | 0.00006846 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | evidence-summary | 1 | 1/0/0 | 100.0 | 100.0 | 1246.0 | 1246 | 0.00006202 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | policy-ladder-check | 1 | 1/0/0 | 100.0 | 100.0 | 2255.0 | 2255 | 0.00008470 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 1 | 1/0/0 | 100.0 | 100.0 | 818.0 | 818 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | evidence-summary | 1 | 1/0/0 | 100.0 | 100.0 | 713.0 | 713 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | policy-ladder-check | 1 | 1/0/0 | 100.0 | 100.0 | 796.0 | 796 | 0.00000000 | 100.0 |
| Stage_F_multi_agent | anthropic | `claude-fable-5` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 6332.6 | 6143 | 0.01686800 | 100.0 |
| Stage_F_multi_agent | deepseek | `deepseek-chat` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1801.6 | 1950 | 0.00009884 | 100.0 |
| Stage_F_multi_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1535.4 | 1126 | 0.00000000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
