# KPI Plan for Journal Validation

This file defines the scientific KPIs required to turn the ZKTrustLLM-Agents L4 demo into a journal-grade evaluation.

## 1. Network / O-RAN Edge KPIs

| KPI | Unit | Purpose |
|---|---:|---|
| RTP packet rate | packets/s | Measures live media-plane flow intensity. |
| RTP jitter | ms | Measures timing instability. |
| RTP loss | % | Detects impaired media delivery. |
| DTLS-RTP jitter | ms | Measures secure media timing overhead. |
| DTLS-RTP loss | % | Measures secure media degradation. |
| bitrate | kbps | Measures media throughput. |
| impairment profile | label | clean, delay, jitter, loss scenarios. |

## 2. Agentic AI KPIs

| KPI | Unit | Purpose |
|---|---:|---|
| reasoning latency | ms | Time for agent reasoning/classification. |
| A2A reference size | bytes | Measures inter-agent reference overhead. |
| trust state | label | Trusted, Restricted, Isolate. |
| action class | label | AUTOMATIC, HUMAN, PRIVILEGED, NEVER. |
| approval queue count | count | Human-governance pressure. |
| action outcome | label | executed, queued, blocked. |

## 3. ZK Proof KPIs

| KPI | Unit | Purpose |
|---|---:|---|
| AUTH version | label | AUTH_V2, V2.1, V2.2, V2.3. |
| public input count | count | Circuit public-state complexity. |
| prover time | ms | Proof-generation overhead. |
| verifier gas | gas | On-chain verification cost. |
| positive proof result | pass/fail | Correct proof acceptance. |
| mutated proof result | pass/fail | Negative proof rejection. |
| policyAdmissibleFlag | 0/1 | Formal admissibility output. |

## 4. Blockchain / Trust-Plane KPIs

| KPI | Unit | Purpose |
|---|---:|---|
| chain id | id | Local/testnet identity. |
| block number | count | Anchor placement. |
| anchor gas | gas | Trust-plane storage cost. |
| transaction hash | hash | Public/local audit reference. |
| ledger hash | hash | Hash-chain final state. |
| IPFS CID | CID | Cold-path evidence reference. |
| replay rejected | bool | Duplicate-anchor defence. |
| zero anchor rejected | bool | Empty-anchor defence. |
| unauthorized submitter rejected | bool | RBAC/capability defence. |

## 5. Ablation KPIs

| Variant | Removed feature | Expected measurable effect |
|---|---|---|
| Full L4 | none | strongest accountability, highest overhead |
| No-ZK | AUTH proof removed | lower latency/gas, weaker verifiability |
| Oracle-only | proof and policy binding weakened | faster but weaker accountability |
| RBAC-only | proof removed, role gate kept | blocks unauthorized submitters but cannot prove decision validity |
| No-IPFS | content-addressed evidence removed | weaker evidence reproducibility |
| No-policy-gate | governance removed | unsafe escalation possible |

## 6. Statistical Reporting

For each KPI, report:

- mean,
- median,
- standard deviation,
- minimum,
- maximum,
- p50,
- p95,
- number of repeated runs,
- pass/fail count,
- rejection rate where relevant.

## 7. Required Paper Tables

- Table I: quantitative novelty/comparison matrix.
- Table II: formal verification result matrix.
- Table III: demo KPI summary.
- Table IV: ablation study.
- Table V: access-control comparison.
- Table VI: blockchain/test-mode comparison.
- Table VII: threat-response validation.
