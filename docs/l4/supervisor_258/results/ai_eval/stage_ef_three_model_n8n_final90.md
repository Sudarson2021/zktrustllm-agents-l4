# stage_ef_three_model_n8n_final90

Generated: 2026-07-04T16:23:15
Total measured records: 90

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 5596.4 | 5761 | 0.01383000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 4393.8 | 4507 | 0.01064000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 6363.6 | 6966 | 0.01994000 | 20.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1429.0 | 1636 | 0.00006846 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 1360.8 | 1350 | 0.00005642 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | policy-ladder-check | 5 | 4/1/0 | 100.0 | 96.0 | 2252.0 | 2354 | 0.00007658 | 20.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1271.4 | 1876 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 1267.2 | 1832 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 1871.0 | 2662 | 0.00000000 | 40.0 |
| Stage_F_multi_agent | anthropic | `claude-fable-5` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 5144.4 | 6041 | 0.01678133 | 100.0 |
| Stage_F_multi_agent | deepseek | `deepseek-chat` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1658.1 | 1801 | 0.00009675 | 100.0 |
| Stage_F_multi_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1455.2 | 2356 | 0.00000000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
