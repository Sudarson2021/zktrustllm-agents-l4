# Step 93 Network Namespace: Plain RTP vs DTLS-Wrapped RTP

## Purpose

This step reproduces the Step 91 network-impairment experiment using two Linux network namespaces instead of localhost-only loopback.

The purpose is to strengthen the media-plane evaluation by separating the sender and receiver into isolated network stacks connected through a veth pair.

## Namespace Topology

The experiment creates:

- Sender namespace: `zkl4_sender`
- Receiver namespace: `zkl4_receiver`
- Sender IP: `10.93.0.1`
- Receiver IP: `10.93.0.2`
- Sender veth: `zkl4veth_s`
- Receiver veth: `zkl4veth_r`

```text
zkl4_sender / 10.93.0.1  <---- veth pair ---->  zkl4_receiver / 10.93.0.2
Compared Modes

The experiment compares:

Plain RTP over the namespace veth path
DTLS-wrapped RTP over the namespace veth path
Impairment Profiles

The experiment uses Linux tc netem on the namespace veth links.

The tested profiles are:

clean baseline
20 ms fixed delay
20 ms delay with 5 ms jitter
30 ms delay, 10 ms jitter, and 1% packet loss
Measured KPIs

The experiment measures:

received RTP packets
expected RTP packets
lost RTP packets
packet-loss percentage
average bitrate
arrival-gap jitter
p50 jitter
p95 jitter
maximum jitter
Corrected Sequence-Loss Calculation

Packet loss is computed using circular RTP sequence-number analysis. This avoids false 65536-packet loss when packet reordering or RTP sequence wrap-around occurs under tc netem jitter.

Measured Result Summary

The corrected Step 93 results show:

0.0% packet loss under clean baseline and fixed-delay profiles.
0.0% packet loss under the 20 ms delay plus 5 ms jitter profile.
Approximately 1% packet loss under the 30 ms delay, 10 ms jitter, and 1% loss profile.
DTLS-wrapped RTP remains measurable and stable under the namespace impairment profiles.
Research Meaning

Step 93 strengthens the media-plane evaluation because it moves the Step 91 impairment experiment from localhost loopback to an isolated two-node namespace topology.

This provides stronger evidence that the Level 4 architecture can connect proof-governed control-plane coordination with measurable secured media-plane behaviour under controlled network stress.

Boundary

This is still a single-machine namespace experiment. The next stage should reproduce the same matrix across two physical devices, a university testbed, Mininet, or ns-3.
