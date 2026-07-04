# stage_ef_three_model_n8n_final90

Generated: 2026-07-04T16:12:47
Total measured records: 90

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 5723.2 | 5781 | 0.01354000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 4345.4 | 4374 | 0.01056000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 6470.6 | 6246 | 0.02025000 | 20.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | claim-boundary-review | 5 | 4/1/0 | 100.0 | 96.7 | 1361.0 | 1482 | 0.00006852 | 80.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 1412.6 | 1514 | 0.00006202 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 2242.6 | 2457 | 0.00007720 | 20.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1269.4 | 1843 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 961.8 | 864 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 1394.8 | 1860 | 0.00000000 | 20.0 |
| Stage_F_multi_agent | anthropic | `claude-fable-5` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 4961.7 | 5356 | 0.01652467 | 100.0 |
| Stage_F_multi_agent | deepseek | `deepseek-chat` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1385.3 | 1535 | 0.00009623 | 100.0 |
| Stage_F_multi_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1467.3 | 2047 | 0.00000000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
