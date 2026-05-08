# Step 90 DTLS-Wrapped RTP Media-Plane Telemetry Summary

> This experiment measures RTP media packets protected by a local DTLS tunnel/proxy. It is not WebRTC DTLS-SRTP.

## Summary

- Capture duration: 25 seconds
- RTP client input: 127.0.0.1:6000
- DTLS endpoint: 127.0.0.1:4444
- Recovered RTP endpoint: 127.0.0.1:5006
- Received packets: 769
- Average bitrate: 102.17 kbps
- Expected packets: 769
- Lost packets: 0
- Packet loss: 0.0%
- Jitter metric: arrival-gap jitter component
- Median arrival gap: 33.3325 ms
- Average jitter component: 0.95001 ms
- P50 jitter component: 0.1185 ms
- Max jitter component: 33.3165 ms

## Comparison with Step 89 Plain RTP

- Plain RTP packet loss: 0.0%
- DTLS-wrapped RTP packet loss: 0.0%
- Plain RTP average bitrate: 833.605 kbps
- DTLS-wrapped RTP average bitrate: 102.17 kbps
- Plain RTP average jitter: 0.229169 ms
- DTLS-wrapped RTP arrival-gap jitter: 0.95001 ms

## Research Meaning

This step adds the first secured media-plane validation layer after the plain RTP baseline. The DTLS handshake succeeds, recovered RTP packets are captured, and packet-loss/jitter/bitrate KPIs are measured after DTLS protection.

## Boundary

This is a DTLS tunnel/proxy baseline for RTP media-plane validation. It is not WebRTC DTLS-SRTP.
