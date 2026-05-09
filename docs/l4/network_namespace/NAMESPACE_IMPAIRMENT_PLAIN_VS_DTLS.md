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

Topology:

```text
zkl4_sender / 10.93.0.1  <---- veth pair ---->  zkl4_receiver / 10.93.0.2

---

## Step 93 Fix D: clean the malformed paper Section 19

Your current `docs/paper/l4_mcp_a2a_evaluation_section.md` has duplicated/malformed Section 19 text. Replace only the bad Section 19 block:

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("docs/paper/l4_mcp_a2a_evaluation_section.md")
s = p.read_text()

marker = "## 19. Namespace-Based Media-Plane Impairment Validation"

if marker in s:
    s = s[:s.index(marker)].rstrip() + "\n\n"

clean = r'''## 19. Namespace-Based Media-Plane Impairment Validation

Step 93 reproduces the Step 91 media-plane impairment evaluation using two Linux network namespaces connected by a veth pair.

This experiment separates the media sender and media receiver into isolated network stacks. Plain RTP and DTLS-wrapped RTP are evaluated under controlled `tc netem` impairment profiles, including fixed delay, jitter, and packet loss.

This step strengthens the evaluation because Step 91 used localhost loopback, while Step 93 introduces an explicit sender-receiver network path. The result is closer to a two-node media-plane deployment while remaining reproducible on a single development machine.

The measured KPIs include packet loss, bitrate, arrival-gap jitter, p50 jitter, p95 jitter, and received packet count. Jitter is computed from packet arrival-gap variation to avoid misleading raw RTP timestamp artefacts caused by H.264 packet ordering. Packet loss is computed using circular RTP sequence-number analysis to avoid false loss inflation under packet reordering or sequence wrap-around.

Step 93 therefore provides a stronger bridge between the proof-governed MCP/A2A control-plane workflow and secured multimedia delivery under network stress.
'''

p.write_text(s + clean + "\n")
print("Cleaned and rewrote Section 19.")
PY
grep -q "Table 17: Step 93 Namespace-Based Plain RTP vs DTLS-RTP Result Files" docs/paper/l4_results_tables.md || cat >> docs/paper/l4_results_tables.md <<'EOF'

## Table 17: Step 93 Namespace-Based Plain RTP vs DTLS-RTP Result Files

| Artifact | Path |
|---|---|
| Step 93 namespace summary JSON | `results/l4_namespace_impairment/namespace_impairment_summary.json` |
| Step 93 namespace summary CSV | `results/l4_namespace_impairment/namespace_impairment_summary.csv` |
| Step 93 namespace summary Markdown | `results/l4_namespace_impairment/namespace_impairment_summary.md` |
| Figure 5.19 namespace packet loss | `results/l4_namespace_impairment/figure_5_19_namespace_packet_loss.png` |
| Figure 5.20 namespace bitrate | `results/l4_namespace_impairment/figure_5_20_namespace_bitrate.png` |
| Figure 5.21 namespace arrival-gap jitter | `results/l4_namespace_impairment/figure_5_21_namespace_arrival_gap_jitter.png` |

Step 93 reproduces the Step 91 plain RTP vs DTLS-wrapped RTP impairment matrix using two Linux network namespaces connected through a veth pair. This improves realism compared with localhost-only loopback while preserving controlled reproducibility.
