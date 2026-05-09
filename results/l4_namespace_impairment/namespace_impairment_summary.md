# Step 93 Network Namespace: Plain RTP vs DTLS-Wrapped RTP
## Purpose
This experiment reproduces the Step 91 media-plane impairment matrix using two Linux network namespaces connected by a veth pair.
## Namespace Topology
- Sender namespace: `zkl4_sender` with IP `10.93.0.1`
- Receiver namespace: `zkl4_receiver` with IP `10.93.0.2`
- Sender veth: `zkl4veth_s`
- Receiver veth: `zkl4veth_r`
## Measurement Note
Jitter is computed from packet arrival-gap variation to avoid misleading raw RTP timestamp artefacts from H.264 packet ordering.
## Results
| Profile | Mode | Packets | Loss % | Bitrate kbps | Avg jitter ms | P50 jitter ms | P95 jitter ms |
|---|---|---:|---:|---:|---:|---:|---:|
| clean_baseline | plain_rtp_namespace | 752 | 0.0 | 100.40384 | 1.551511 | 0.114528 | 0.399285 |
| clean_baseline | dtls_rtp_namespace | 692 | 0.0 | 92.76512 | 1.702097 | 0.144913 | 0.657679 |
| delay_20ms | plain_rtp_namespace | 752 | 0.0 | 100.40384 | 1.543121 | 0.117319 | 0.405098 |
| delay_20ms | dtls_rtp_namespace | 691 | 0.0 | 92.70176 | 1.729853 | 0.146429 | 1.311308 |
| delay_20ms_jitter_5ms | plain_rtp_namespace | 752 | 0.0 | 100.40384 | 7.032225 | 5.147237 | 18.951567 |
| delay_20ms_jitter_5ms | dtls_rtp_namespace | 691 | 0.0 | 92.70176 | 6.745149 | 4.977152 | 20.902422 |
| delay_30ms_jitter_10ms_loss_1pct | plain_rtp_namespace | 744 | 0.932091 | 99.22016 | 12.334627 | 10.499932 | 30.573148 |
| delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_namespace | 684 | 0.869565 | 91.96128 | 12.014682 | 10.072966 | 30.424974 |

## Research Meaning
Step 93 strengthens Step 91 by moving the impairment experiment from localhost loopback to an isolated two-namespace topology. This is closer to a real two-node media-plane path and is more suitable for journal evaluation.

## Boundary
This is still a single-machine namespace test. The next stage should reproduce the same matrix across two physical machines, a university testbed, Mininet, or ns-3.
