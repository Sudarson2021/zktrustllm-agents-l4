# Multi-Model n8n Tool-Scenario Results

Generated at: 2026-07-04T12:58:36Z
Input records: 90

Only live rows with raw provider responses are paper evidence. `SKIPPED_NO_API_KEY` rows document missing credentials and are not reported as model results.

| Provider | Model | Tool scenario | Live runs | Validator pass % | JSON % | Schema % | Claim-boundary match % | Ladder violations | Mean latency ms | p95 latency ms | Mean output tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude | `claude-haiku-4-5-20251001` | claim-boundary-review | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 3982.6 | 4400.3 | 411.8 |
| claude | `claude-haiku-4-5-20251001` | evidence-summary | 10 | 0.0 | 100.0 | 100.0 | 0.0 | 0 | 5813.0 | 10287.6 | 536.9 |
| claude | `claude-haiku-4-5-20251001` | policy-ladder-check | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 3467.4 | 4000.0 | 295.0 |
| deepseek | `deepseek-chat` | claim-boundary-review | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 2235.6 | 2498.7 | 199.2 |
| deepseek | `deepseek-chat` | evidence-summary | 10 | 0.0 | 100.0 | 100.0 | 0.0 | 0 | 2258.9 | 2380.7 | 192.4 |
| deepseek | `deepseek-chat` | policy-ladder-check | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 1477.6 | 1653.6 | 90.0 |
| mistral | `mistral-small-latest` | claim-boundary-review | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 1489.9 | 1715.1 | 216.4 |
| mistral | `mistral-small-latest` | evidence-summary | 10 | 100.0 | 100.0 | 100.0 | 100.0 | 0 | 1342.0 | 1536.3 | 181.2 |
| mistral | `mistral-small-latest` | policy-ladder-check | 10 | 0.0 | 100.0 | 100.0 | 100.0 | 0 | 875.4 | 941.4 | 103.5 |
