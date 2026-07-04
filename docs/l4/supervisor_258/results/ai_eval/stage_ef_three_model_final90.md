# stage_ef_three_model_final90

Generated: 2026-07-04T15:42:52
Total measured records: 90

| Stage | Provider | Model | Scenario/Case | Runs | Pass/Partial/Fail | Valid JSON % | Mean accuracy % | Mean latency ms | p95 latency ms | Mean cost/run USD | Consistency % |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Stage_E_single_agent | anthropic | `claude-fable-5` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 6590.4 | 6042 | 0.01347000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 4911.6 | 5483 | 0.01058000 | 100.0 |
| Stage_E_single_agent | anthropic | `claude-fable-5` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 6255.6 | 6450 | 0.02000000 | 20.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1377.0 | 1432 | 0.00006846 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 1462.0 | 1547 | 0.00005866 | 100.0 |
| Stage_E_single_agent | deepseek | `deepseek-chat` | policy-ladder-check | 5 | 4/1/0 | 100.0 | 96.0 | 1939.8 | 2048 | 0.00007658 | 20.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 5 | 5/0/0 | 100.0 | 100.0 | 1341.2 | 1790 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | evidence-summary | 5 | 5/0/0 | 100.0 | 100.0 | 1043.8 | 921 | 0.00000000 | 100.0 |
| Stage_E_single_agent | mistral | `mistral-medium-latest` | policy-ladder-check | 5 | 5/0/0 | 100.0 | 100.0 | 1650.2 | 2637 | 0.00000000 | 40.0 |
| Stage_F_multi_agent | anthropic | `claude-fable-5` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 5405.6 | 6386 | 0.01668467 | 100.0 |
| Stage_F_multi_agent | deepseek | `deepseek-chat` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1418.6 | 1739 | 0.00009731 | 100.0 |
| Stage_F_multi_agent | mistral | `mistral-medium-latest` | claim-boundary-review | 15 | 15/0/0 | 100.0 | 100.0 | 1276.8 | 2150 | 0.00000000 | 100.0 |

## Claim boundary

These results evaluate AI-model/tool and multi-agent orchestration behaviour around the local ZKTrustLLM-Agents L4 n8n artifact. They are not production O-RAN deployment, packet-capture network benchmarking, public-chain benchmarking, or full media-plane QoE validation.
