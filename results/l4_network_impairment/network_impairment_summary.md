# Step 91 Network Impairment: Plain RTP vs DTLS-Wrapped RTP

## Purpose

This experiment compares plain RTP and DTLS-wrapped RTP media-plane behaviour under controlled loopback impairment using Linux `tc netem`.

## Important Measurement Note

The Step 91 matrix computes jitter from packet arrival-gap variation. This avoids misleading raw RTP timestamp artefacts from H.264 packet ordering.

## Results

| Profile | Mode | Packets | Loss % | Bitrate kbps | Avg jitter ms | P50 jitter ms | P95 jitter ms |
|---|---|---:|---:|---:|---:|---:|---:|
| clean_baseline | plain_rtp | 2328 | 0.0 | 833.60512 | 10.709105 | 0.045 | 34.019 |
| clean_baseline | dtls_rtp | 769 | 0.0 | 102.16992 | 0.926337 | 0.1165 | 0.4245 |
| delay_20ms | plain_rtp | 2328 | 0.0 | 833.60512 | 10.703096 | 0.057 | 33.846 |
| delay_20ms | dtls_rtp | 769 | 0.0 | 102.41888 | 0.98316 | 0.1665 | 0.5325 |
| delay_20ms_jitter_5ms | plain_rtp | 2328 | 28.698315 | 833.70944 | 8.326312 | 4.855 | 24.453 |
| delay_20ms_jitter_5ms | dtls_rtp | 769 | 2.411168 | 102.41888 | 10.276802 | 8.8005 | 24.8545 |
| delay_30ms_jitter_10ms_loss_1pct | plain_rtp | 2300 | 28.549239 | 823.69248 | 6.975492 | 5.834 | 19.719 |
| delay_30ms_jitter_10ms_loss_1pct | dtls_rtp | 737 | 13.700234 | 98.3696 | 17.46476 | 15.8885 | 37.8075 |

## Research Meaning

Step 91 extends clean RTP and DTLS/RTP media-plane validation by introducing delay, jitter, and packet-loss impairment.
This strengthens the journal evaluation because it compares plain and secured media delivery under controlled network stress.

## Boundary

This remains a localhost loopback impairment experiment. The next stage should reproduce the same setup across two machines, Linux network namespaces, Mininet, or ns-3.

