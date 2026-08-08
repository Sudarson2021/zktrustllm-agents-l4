# Stage A-F + F/F Master Supervisor Summary

Generated: 2026-07-05T00:29:21

## Claim boundary

This master workflow supports local evidence-grounded orchestration, multi-model baseline evaluation, multi-agent test cases, and four-model inter-agent communication. It does not claim production O-RAN deployment validation, packet-capture network benchmarking, public-chain benchmarking, full media-plane QoE validation, or a 240-run six-variant ablation.

## Evidence stages

| Stage | Description | Runs / Records | PASS/PARTIAL/FAIL | Valid JSON | Mean accuracy % | Mean latency ms | Mean cost USD |
|---|---|---:|---|---:|---:|---:|---:|
| A | Experiment initialisation and claim boundary | -- | -- | -- | -- | -- | -- |
| B | Local repeatability | 12 | -- | -- | -- | -- | -- |
| C | Local profile-pilot | 24 | -- | -- | -- | -- | -- |
| D-real | Local real-variant matrix | 120 | -- | -- | -- | -- | -- |
| E/F | Three-model AI evaluation | 90 | 89/1/0 | 90 | 99.78 | 2809.9 | 0.00529143 |
| F/F | Four-model inter-agent communication | 15 | 15/0/0 | 15 | 100.0 | 30717.07 | 0.06894651 |

Frozen local evidence total before AI-assisted stages: **156 runs**.

## Stage F/F scenario results

| Scenario | Runs | PASS/PARTIAL/FAIL | Valid JSON | Mean accuracy % | Mean latency ms | Mean cost USD |
|---|---:|---|---:|---:|---:|---:|
| agent-collaboration | 3 | 3/0/0 | 3 | 100.0 | 31059.33 | 0.06794774 |
| failure-recovery | 3 | 3/0/0 | 3 | 100.0 | 30578.67 | 0.06947253 |
| model-disagreement-resolution | 3 | 3/0/0 | 3 | 100.0 | 29864.67 | 0.06845889 |
| task-decomposition | 3 | 3/0/0 | 3 | 100.0 | 30301.67 | 0.06948338 |
| verification-agent | 3 | 3/0/0 | 3 | 100.0 | 31781.0 | 0.06937001 |

## Supervisor feedback coverage

- n8n workflow diagram
- workflow logic explanation
- role of each component
- Claude, DeepSeek, and Mistral scenarios
- GPT-5.5, Claude, DeepSeek, and Mistral inter-agent communication
- task decomposition
- agent collaboration
- failure recovery
- verification agent
- model disagreement resolution
- accuracy
- execution time
- cost
- failed runs
- consistency
- single-agent baseline comparison
