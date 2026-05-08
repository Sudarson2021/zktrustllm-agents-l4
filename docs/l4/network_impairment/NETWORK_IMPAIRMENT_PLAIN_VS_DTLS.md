# Step 91 Network Impairment: Plain RTP vs DTLS-Wrapped RTP

## Purpose

This step evaluates media-plane behaviour under controlled network impairment.

It extends:

- Step 89: live plain RTP media-plane telemetry
- Step 90: DTLS-wrapped RTP media-plane validation

The goal is to compare plain RTP and DTLS-wrapped RTP under delay, jitter, and packet-loss conditions.

## Experimental Method

The experiment uses Linux `tc netem` on the loopback interface.

For each impairment profile, the workflow runs:

1. Plain RTP telemetry
2. DTLS-wrapped RTP telemetry

The script then extracts and compares:

- received RTP packets,
- packet loss,
- average bitrate,
- arrival-gap jitter.

## Measurement Note

Jitter is calculated from packet arrival-gap variation rather than raw RTP timestamp deltas.

This avoids misleading artefacts caused by H.264 RTP timestamp ordering and packetisation behaviour.

## Impairment Profiles

The evaluated profiles are:

1. `clean_baseline`
2. `delay_20ms`
3. `delay_20ms_jitter_5ms`
4. `delay_30ms_jitter_10ms_loss_1pct`

## Generated Artifacts

- Summary JSON:
  - `results/l4_network_impairment/network_impairment_summary.json`

- Summary CSV:
  - `results/l4_network_impairment/network_impairment_summary.csv`

- Summary Markdown:
  - `results/l4_network_impairment/network_impairment_summary.md`

- Figures:
  - `results/l4_network_impairment/figure_5_16_plain_vs_dtls_impairment_packet_loss.png`
  - `results/l4_network_impairment/figure_5_17_plain_vs_dtls_impairment_bitrate.png`
  - `results/l4_network_impairment/figure_5_18_plain_vs_dtls_impairment_jitter.png`

## Research Meaning

Step 91 moves the evaluation beyond clean localhost media-plane validation.

It gives journal-ready evidence for how the media plane behaves when delay, jitter, and packet loss are introduced.

This is important because the Level 4 architecture is not only a blockchain/MCP/A2A proof-governed control system. It is also intended to support secure multimedia delivery decisions in 5G/6G and O-RAN environments.

## Boundary

This experiment uses loopback impairment. The next stage should reproduce the same tests across:

- two physical machines,
- Linux network namespaces,
- Mininet,
- ns-3, or
- a university testbed network.
