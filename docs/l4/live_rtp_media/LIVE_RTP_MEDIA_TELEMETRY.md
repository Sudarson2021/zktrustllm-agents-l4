# Step 89 Live RTP Media-Plane Telemetry

## Purpose

This step adds live RTP media-plane telemetry to the Level 4 ZKTrustLLM-Agents evaluation workflow.

Previous steps measured MCP/A2A control-plane behaviour, semi-live control-loop latency, and multi-agent scaling. Step 89 begins validating the multimedia delivery plane by measuring RTP packet continuity, RTP jitter, bitrate, and packet loss.

## Experimental Setup

A deterministic 30-second test video is generated using FFmpeg and streamed over RTP on localhost.

The RTP endpoint is:

- Host: `127.0.0.1`
- Port: `5004`

The media sender uses FFmpeg to stream H.264 video over RTP. A Python receiver captures RTP packets directly from the UDP socket and extracts RTP sequence numbers, timestamps, packet sizes, and arrival times.

## Measured KPIs

The experiment measures:

- RTP packet count,
- RTP sequence continuity,
- packet loss,
- RTP jitter component,
- average bitrate,
- RTP packet size,
- RTP timestamp progression.

## Measured Results

| KPI | Result |
|---|---:|
| Capture duration | 25 seconds |
| Received RTP packets | 2328 |
| Expected RTP packets | 2328 |
| Lost packets | 0 |
| Packet loss | 0.0% |
| Average bitrate | 833.605 kbps |
| Average jitter component | 0.229169 ms |
| P50 jitter component | 0.069357 ms |
| Maximum jitter component | 4.163946 ms |

## Generated Artifacts

- RTP packet events:
  - `results/l4_live_rtp_media/rtp_packet_events.csv`

- RTP summary:
  - `results/l4_live_rtp_media/rtp_media_summary.json`
  - `results/l4_live_rtp_media/rtp_media_summary.md`

- Figures:
  - `results/l4_live_rtp_media/figure_5_10_live_rtp_jitter.png`
  - `results/l4_live_rtp_media/figure_5_11_live_rtp_bitrate.png`
  - `results/l4_live_rtp_media/figure_5_12_live_rtp_sequence_progress.png`

## Research Meaning

This step provides the first live media-plane evidence for the Level 4 workflow.

It shows that the project can now measure actual RTP packet delivery behaviour, not only blockchain, MCP, A2A, and proof-layer behaviour.

This is important for the journal direction because Level 4 is intended to connect proof-governed agent decisions with network/media control outcomes.

## Boundary

This experiment validates live RTP media-plane telemetry over localhost.

It is not yet DTLS-secured.

The next step should add DTLS-secured RTP validation so that packet-level media KPIs can be compared before and after secure transport.
