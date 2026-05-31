# Supervisor 258 n8n Evaluation Summary

Total records: 264

## Variant/Profile Summary

| Variant | Profile | Runs | Pass | Fail |
|---|---|---:|---:|---:|
| full_l4 | clean_baseline | 12 | 12 | 0 |
| full_l4 | delay_20ms | 10 | 10 | 0 |
| full_l4 | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | 12 | 12 | 0 |
| no_ipfs | clean_baseline | 12 | 12 | 0 |
| no_ipfs | delay_20ms | 10 | 10 | 0 |
| no_ipfs | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | 12 | 12 | 0 |
| no_policy_gate | clean_baseline | 12 | 12 | 0 |
| no_policy_gate | delay_20ms | 10 | 10 | 0 |
| no_policy_gate | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | 12 | 12 | 0 |
| no_zk | clean_baseline | 12 | 12 | 0 |
| no_zk | delay_20ms | 10 | 10 | 0 |
| no_zk | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | 12 | 12 | 0 |
| oracle_only | clean_baseline | 12 | 12 | 0 |
| oracle_only | delay_20ms | 10 | 10 | 0 |
| oracle_only | delay_20ms_jitter_5ms | 10 | 10 | 0 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | 12 | 12 | 0 |
| rbac_only | clean_baseline | 12 | 0 | 12 |
| rbac_only | delay_20ms | 10 | 0 | 10 |
| rbac_only | delay_20ms_jitter_5ms | 10 | 0 | 10 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | 12 | 0 | 12 |

## Numeric KPI Summary

| Variant | Profile | KPI | n | mean | median | std | p95 |
|---|---|---|---:|---:|---:|---:|---:|
| full_l4 | clean_baseline | duration_ms | 12 | 37950.2500 | 38484.0000 | 3465.5941 | 41816.0000 |
| full_l4 | delay_20ms | duration_ms | 10 | 47435.9000 | 47151.5000 | 2527.7974 | 51309.0000 |
| full_l4 | delay_20ms_jitter_5ms | duration_ms | 10 | 56881.0000 | 57057.0000 | 3152.0605 | 60967.0000 |
| full_l4 | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 61564.9167 | 65600.5000 | 12674.0652 | 70515.0000 |
| no_ipfs | clean_baseline | duration_ms | 12 | 1809.8333 | 1791.0000 | 161.8646 | 2101.0000 |
| no_ipfs | delay_20ms | duration_ms | 10 | 1742.6000 | 1766.5000 | 95.3965 | 1858.0000 |
| no_ipfs | delay_20ms_jitter_5ms | duration_ms | 10 | 1759.8000 | 1779.0000 | 96.6273 | 1875.0000 |
| no_ipfs | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 1754.1667 | 1769.0000 | 89.8026 | 1850.0000 |
| no_policy_gate | clean_baseline | duration_ms | 12 | 1730.5833 | 1774.5000 | 98.0839 | 1811.0000 |
| no_policy_gate | delay_20ms | duration_ms | 10 | 1769.1000 | 1792.0000 | 179.5448 | 2164.0000 |
| no_policy_gate | delay_20ms_jitter_5ms | duration_ms | 10 | 1739.7000 | 1774.0000 | 80.9815 | 1835.0000 |
| no_policy_gate | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 1743.6667 | 1751.5000 | 86.3695 | 1870.0000 |
| no_zk | clean_baseline | duration_ms | 12 | 1775.0833 | 1790.0000 | 99.0789 | 1893.0000 |
| no_zk | delay_20ms | duration_ms | 10 | 1754.2000 | 1778.5000 | 105.4881 | 1928.0000 |
| no_zk | delay_20ms_jitter_5ms | duration_ms | 10 | 1727.6000 | 1765.0000 | 98.7457 | 1832.0000 |
| no_zk | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 1777.0833 | 1786.5000 | 160.1156 | 1856.0000 |
| oracle_only | clean_baseline | duration_ms | 12 | 1770.4167 | 1761.5000 | 158.0233 | 1836.0000 |
| oracle_only | delay_20ms | duration_ms | 10 | 1752.8000 | 1784.0000 | 84.7700 | 1854.0000 |
| oracle_only | delay_20ms_jitter_5ms | duration_ms | 10 | 1783.4000 | 1789.0000 | 139.0110 | 2066.0000 |
| oracle_only | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 1750.0833 | 1764.0000 | 132.6770 | 1897.0000 |
| rbac_only | clean_baseline | duration_ms | 12 | 3504.5000 | 3539.5000 | 82.0338 | 3563.0000 |
| rbac_only | delay_20ms | duration_ms | 10 | 3495.5000 | 3487.0000 | 111.7649 | 3705.0000 |
| rbac_only | delay_20ms_jitter_5ms | duration_ms | 10 | 3472.1000 | 3453.5000 | 76.4976 | 3586.0000 |
| rbac_only | delay_30ms_jitter_10ms_loss_1pct | duration_ms | 12 | 3491.0000 | 3453.0000 | 196.8382 | 3659.0000 |