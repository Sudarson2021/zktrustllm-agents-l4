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
| clean_baseline | plain_rtp_namespace | 752 | 0.0 | 100.40384 | 1.536205 | 0.088882 | 0.793267 |
| clean_baseline | dtls_rtp_namespace | 692 | 0.0 | 92.76512 | 1.698414 | 0.143854 | 0.664744 |
| delay_20ms | plain_rtp_namespace | 752 | 0.0 | 100.40384 | 1.566748 | 0.123351 | 0.866672 |
| delay_20ms | dtls_rtp_namespace | 691 | 0.0 | 92.70176 | 1.718602 | 0.141134 | 2.48888 |
| delay_20ms_jitter_5ms | plain_rtp_namespace | 752 | 98.852539 | 100.40384 | 6.528746 | 4.772306 | 19.314009 |
| delay_20ms_jitter_5ms | dtls_rtp_namespace | 691 | 98.945618 | 92.70176 | 6.871128 | 4.975052 | 20.830896 |
| delay_30ms_jitter_10ms_loss_1pct | plain_rtp_namespace | 746 | 98.861694 | 99.98592 | 12.425314 | 10.433133 | 31.055114 |
| delay_30ms_jitter_10ms_loss_1pct | dtls_rtp_namespace | 687 | 98.951721 | 92.1952 | 11.723093 | 9.525314 | 30.960581 |

## Research Meaning
Step 93 strengthens Step 91 by moving the impairment experiment from localhost loopback to an isolated two-namespace topology. This is closer to a real two-node media-plane path and is more suitable for journal evaluation.

## Boundary
This is still a single-machine namespace test. The next stage should reproduce the same matrix across two physical machines, a university testbed, Mininet, or ns-3.
