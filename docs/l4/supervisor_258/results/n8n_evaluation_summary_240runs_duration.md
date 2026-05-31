# Supervisor 258 n8n Evaluation Summary

Dataset type: deduplicated clean 240-run duration dataset

Raw records found before deduplication: 304
Clean records after keeping latest variant/profile/repeat: 240

## Variant/Profile Summary

| Variant | Profile | Runs | Pass | Fail |
|---|---|---:|---:|---:|
| full_l4 | clean_baseline | 10 | 10 | 0 |
| full_l4 | delay_20ms | 10 | 10 | 0 |
| full_l4 | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |
| no_ipfs | clean_baseline | 10 | 10 | 0 |
| no_ipfs | delay_20ms | 10 | 10 | 0 |
| no_ipfs | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |
| no_policy_gate | clean_baseline | 10 | 10 | 0 |
| no_policy_gate | delay_20ms | 10 | 10 | 0 |
| no_policy_gate | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |
| no_zk | clean_baseline | 10 | 10 | 0 |
| no_zk | delay_20ms | 10 | 10 | 0 |
| no_zk | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |
| oracle_only | clean_baseline | 10 | 10 | 0 |
| oracle_only | delay_20ms | 10 | 10 | 0 |
| oracle_only | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |
| rbac_only | clean_baseline | 10 | 10 | 0 |
| rbac_only | delay_20ms | 10 | 10 | 0 |
| rbac_only | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | 10 | 10 | 0 |

## Numeric KPI Summary

| Variant | Profile | KPI | n | mean | median | std | p95 |
|---|---|---|---:|---:|---:|---:|---:|
| full_l4 | clean_baseline | duration_ms | 10 | 39055.4000 | 39050.5000 | 2504.9154 | 42172.0000 |
| full_l4 | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| full_l4 | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| full_l4 | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | clean_baseline | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | clean_baseline | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| full_l4 | delay_20ms | duration_ms | 10 | 47435.9000 | 47151.5000 | 2527.7974 | 51309.0000 |
| full_l4 | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| full_l4 | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| full_l4 | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_20ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| full_l4 | delay_20ms_jitter_5ms | duration_ms | 10 | 56881.0000 | 57057.0000 | 3152.0605 | 60967.0000 |
| full_l4 | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| full_l4 | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| full_l4 | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_20ms_jitter_5ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 66822.6000 | 67129.0000 | 3457.2336 | 72219.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | clean_baseline | duration_ms | 10 | 1782.7000 | 1772.0000 | 147.4480 | 2118.0000 |
| no_ipfs | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| no_ipfs | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| no_ipfs | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | clean_baseline | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | clean_baseline | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | delay_20ms | duration_ms | 10 | 1742.6000 | 1766.5000 | 95.3965 | 1858.0000 |
| no_ipfs | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| no_ipfs | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| no_ipfs | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_20ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | delay_20ms_jitter_5ms | duration_ms | 10 | 1759.8000 | 1779.0000 | 96.6273 | 1875.0000 |
| no_ipfs | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| no_ipfs | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| no_ipfs | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_20ms_jitter_5ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 1736.5000 | 1760.5000 | 80.2569 | 1850.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | clean_baseline | duration_ms | 10 | 1741.3000 | 1779.5000 | 92.6775 | 1811.0000 |
| no_policy_gate | clean_baseline | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| no_policy_gate | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| no_policy_gate | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | clean_baseline | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | clean_baseline | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | delay_20ms | duration_ms | 10 | 1769.1000 | 1792.0000 | 179.5448 | 2164.0000 |
| no_policy_gate | delay_20ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| no_policy_gate | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| no_policy_gate | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_20ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | duration_ms | 10 | 1739.7000 | 1774.0000 | 80.9815 | 1835.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| no_policy_gate | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 1743.2000 | 1758.0000 | 95.4356 | 1873.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | clean_baseline | duration_ms | 10 | 1765.1000 | 1786.0000 | 106.4429 | 1900.0000 |
| no_zk | clean_baseline | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| no_zk | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| no_zk | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | clean_baseline | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | clean_baseline | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | delay_20ms | duration_ms | 10 | 1754.2000 | 1778.5000 | 105.4881 | 1928.0000 |
| no_zk | delay_20ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| no_zk | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| no_zk | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_20ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | delay_20ms_jitter_5ms | duration_ms | 10 | 1727.6000 | 1765.0000 | 98.7457 | 1832.0000 |
| no_zk | delay_20ms_jitter_5ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| no_zk | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| no_zk | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_20ms_jitter_5ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 1789.3000 | 1797.0000 | 169.6205 | 2190.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | clean_baseline | duration_ms | 10 | 1777.8000 | 1779.0000 | 172.3284 | 2184.0000 |
| oracle_only | clean_baseline | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| oracle_only | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| oracle_only | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | clean_baseline | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | clean_baseline | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | delay_20ms | duration_ms | 10 | 1752.8000 | 1784.0000 | 84.7700 | 1854.0000 |
| oracle_only | delay_20ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| oracle_only | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| oracle_only | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_20ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | delay_20ms_jitter_5ms | duration_ms | 10 | 1783.4000 | 1789.0000 | 139.0110 | 2066.0000 |
| oracle_only | delay_20ms_jitter_5ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| oracle_only | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| oracle_only | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_20ms_jitter_5ms | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 1752.5000 | 1764.0000 | 137.0663 | 1969.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | hardhat_failing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | clean_baseline | duration_ms | 10 | 3311.4000 | 3521.5000 | 398.1516 | 3648.0000 |
| rbac_only | clean_baseline | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | clean_baseline | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | clean_baseline | rtp_jitter_ms | 10 | 0.2000 | 0.2000 | 0.0000 | 0.2000 |
| rbac_only | clean_baseline | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | clean_baseline | dtls_rtp_jitter_ms | 10 | 0.2500 | 0.2500 | 0.0000 | 0.2500 |
| rbac_only | clean_baseline | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | clean_baseline | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | clean_baseline | hardhat_passing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | delay_20ms | duration_ms | 10 | 3579.0000 | 3585.5000 | 130.7015 | 3801.0000 |
| rbac_only | delay_20ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_20ms | rtp_jitter_ms | 10 | 0.5000 | 0.5000 | 0.0000 | 0.5000 |
| rbac_only | delay_20ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms | dtls_rtp_jitter_ms | 10 | 0.6000 | 0.6000 | 0.0000 | 0.6000 |
| rbac_only | delay_20ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_20ms | hardhat_passing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | delay_20ms_jitter_5ms | duration_ms | 10 | 3606.8000 | 3625.0000 | 126.4303 | 3849.0000 |
| rbac_only | delay_20ms_jitter_5ms | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms_jitter_5ms | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_20ms_jitter_5ms | rtp_jitter_ms | 10 | 5.0000 | 5.0000 | 0.0000 | 5.0000 |
| rbac_only | delay_20ms_jitter_5ms | rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms_jitter_5ms | dtls_rtp_jitter_ms | 10 | 5.5000 | 5.5000 | 0.0000 | 5.5000 |
| rbac_only | delay_20ms_jitter_5ms | dtls_rtp_loss_pct | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_20ms_jitter_5ms | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_20ms_jitter_5ms | hardhat_passing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 10 | 3606.6000 | 3600.5000 | 210.2766 | 4123.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | prover_time_ms | 10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | verifier_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | rtp_jitter_ms | 10 | 10.0000 | 10.0000 | 0.0000 | 10.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_jitter_ms | 10 | 10.8000 | 10.8000 | 0.0000 | 10.8000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_loss_pct | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | post_auto_score_gas | 10 | 47913.0000 | 47913.0000 | 0.0000 | 47913.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | hardhat_passing_tests | 10 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |