# Step 90 DTLS-Wrapped RTP Media-Plane Validation

## Purpose

This step extends the Step 89 plain RTP media-plane baseline by adding DTLS protection around RTP delivery.

The goal is to validate that the Level 4 workflow can move from unsecured RTP telemetry to secured media-plane telemetry.

## Experimental Setup

The experiment uses a local DTLS tunnel/proxy:

- FFmpeg sends RTP to the DTLS client proxy.
- The DTLS client protects RTP packets using DTLS.
- The DTLS server receives DTLS records and recovers RTP packets.
- A Python receiver captures recovered RTP packets and computes media-plane KPIs.

This is a controlled DTLS tunnel/proxy baseline. It is not WebRTC DTLS-SRTP.

## Measured KPIs

The experiment measures:

- DTLS handshake success,
- recovered RTP packet count,
- packet loss,
- average bitrate,
- arrival-gap jitter,
- RTP sequence continuity.

## Key Result

The DTLS handshake completed successfully and RTP packets were recovered after DTLS protection.

The current result shows:

- recovered RTP packets: 769,
- packet loss: 0.0%,
- average bitrate: 102.17 kbps.

The jitter metric is computed using arrival-gap variation rather than raw RTP timestamp deltas. This avoids false artefacts caused by non-monotonic H.264 RTP timestamps.

## Research Meaning

This step provides the first secured media-plane validation layer for the Level 4 project.

It connects the previous proof-governed MCP/A2A control-plane evaluation to DTLS-protected multimedia delivery behaviour.

## Boundary

This is a localhost DTLS/RTP tunnel validation. Future work should extend it to:

- DTLS multicast or group-key-protected delivery,
- controlled packet loss and delay using network emulation,
- comparison against Step 89 plain RTP under the same network impairment profile,
- integration with LKH-triggered rekey/isolation actions.
