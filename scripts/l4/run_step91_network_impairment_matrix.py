#!/usr/bin/env python3

import csv
import json
import shutil
import statistics
import subprocess
import time
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "results" / "l4_network_impairment"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PLAIN_SCRIPT = ROOT / "scripts" / "l4" / "run_live_rtp_media_telemetry.py"
DTLS_SCRIPT = ROOT / "scripts" / "l4" / "run_dtls_rtp_media_telemetry.py"

PLAIN_SUMMARY = ROOT / "results" / "l4_live_rtp_media" / "rtp_media_summary.json"
DTLS_SUMMARY = ROOT / "results" / "l4_dtls_rtp_media" / "dtls_rtp_media_summary.json"

PLAIN_EVENTS = ROOT / "results" / "l4_live_rtp_media" / "rtp_packet_events.csv"
DTLS_EVENTS = ROOT / "results" / "l4_dtls_rtp_media" / "dtls_rtp_packet_events.csv"

SUMMARY_JSON = OUT_DIR / "network_impairment_summary.json"
SUMMARY_CSV = OUT_DIR / "network_impairment_summary.csv"
SUMMARY_MD = OUT_DIR / "network_impairment_summary.md"

FIG_LOSS = OUT_DIR / "figure_5_16_plain_vs_dtls_impairment_packet_loss.png"
FIG_BITRATE = OUT_DIR / "figure_5_17_plain_vs_dtls_impairment_bitrate.png"
FIG_JITTER = OUT_DIR / "figure_5_18_plain_vs_dtls_impairment_jitter.png"


PROFILES = [
    {
        "name": "clean_baseline",
        "description": "No artificial impairment on loopback",
        "netem": None,
    },
    {
        "name": "delay_20ms",
        "description": "20 ms fixed delay",
        "netem": ["delay", "20ms"],
    },
    {
        "name": "delay_20ms_jitter_5ms",
        "description": "20 ms delay with 5 ms jitter",
        "netem": ["delay", "20ms", "5ms", "distribution", "normal"],
    },
    {
        "name": "delay_30ms_jitter_10ms_loss_1pct",
        "description": "30 ms delay, 10 ms jitter, 1% packet loss",
        "netem": ["delay", "30ms", "10ms", "distribution", "normal", "loss", "1%"],
    },
]


def run_cmd(cmd, check=True):
    print("+", " ".join(str(x) for x in cmd))
    return subprocess.run(cmd, cwd=ROOT, check=check)


def reset_netem():
    subprocess.run(
        ["sudo", "tc", "qdisc", "del", "dev", "lo", "root"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def apply_profile(profile):
    reset_netem()

    if profile["netem"] is None:
        print(f"[netem] clean profile: {profile['name']}")
        return

    cmd = ["sudo", "tc", "qdisc", "replace", "dev", "lo", "root", "netem"] + profile["netem"]
    run_cmd(cmd)
    print(f"[netem] applied profile: {profile['name']}")


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def read_packet_events(path):
    events = []

    if not path.exists():
        return events

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                arrival_ms = float(row["arrival_ms"])
                sequence = int(row["sequence"]) % 65536
                packet_bytes = int(row["packet_bytes"])
            except Exception:
                continue

            if packet_bytes <= 12:
                continue

            events.append(
                {
                    "arrival_ms": arrival_ms,
                    "sequence": sequence,
                    "packet_bytes": packet_bytes,
                }
            )

    return events


def median(values):
    if not values:
        return 0.0
    return float(statistics.median(values))


def avg(values):
    if not values:
        return 0.0
    return float(statistics.mean(values))


def percentile(values, pct):
    if not values:
        return 0.0

    values = sorted(values)
    idx = int(round((pct / 100.0) * (len(values) - 1)))
    return float(values[idx])


def arrival_gap_jitter(events):
    if len(events) < 2:
        return {
            "samples": 0,
            "medianArrivalGapMs": 0.0,
            "avgJitterMs": 0.0,
            "p50JitterMs": 0.0,
            "p95JitterMs": 0.0,
            "maxJitterMs": 0.0,
        }

    events = sorted(events, key=lambda x: x["arrival_ms"])
    gaps = []

    for prev, cur in zip(events, events[1:]):
        gap = cur["arrival_ms"] - prev["arrival_ms"]
        if gap >= 0:
            gaps.append(gap)

    med_gap = median(gaps)
    jitter = [abs(g - med_gap) for g in gaps]

    return {
        "samples": len(jitter),
        "medianArrivalGapMs": round(med_gap, 6),
        "avgJitterMs": round(avg(jitter), 6),
        "p50JitterMs": round(percentile(jitter, 50), 6),
        "p95JitterMs": round(percentile(jitter, 95), 6),
        "maxJitterMs": round(max(jitter) if jitter else 0.0, 6),
    }


def robust_sequence_loss(events):
    if len(events) < 2:
        return {
            "expectedPackets": len(events),
            "receivedPackets": len(events),
            "lostPackets": 0,
            "packetLossPct": 0.0,
            "ignoredReorderOrWrapEvents": 0,
        }

    events = sorted(events, key=lambda x: x["arrival_ms"])
    sequences = [e["sequence"] for e in events]

    lost = 0
    ignored = 0
    last = sequences[0]

    for seq in sequences[1:]:
        delta = (seq - last) % 65536

        if delta == 0:
            continue

        if 1 <= delta < 30000:
            if delta > 1:
                lost += delta - 1
            last = seq
        else:
            ignored += 1

    received = len(events)
    expected = received + lost
    loss_pct = (lost / expected * 100.0) if expected else 0.0

    return {
        "expectedPackets": expected,
        "receivedPackets": received,
        "lostPackets": lost,
        "packetLossPct": round(loss_pct, 6),
        "ignoredReorderOrWrapEvents": ignored,
    }


def extract_metrics(summary, mode, event_csv):
    events = read_packet_events(event_csv)
    capture_seconds = float(summary.get("captureSeconds", 25))

    if events:
        total_bytes = sum(e["packet_bytes"] for e in events)
        bitrate_kbps = (total_bytes * 8.0) / capture_seconds / 1000.0
        jitter = arrival_gap_jitter(events)
        loss = robust_sequence_loss(events)

        return {
            "mode": mode,
            "receivedPackets": loss["receivedPackets"],
            "expectedPackets": loss["expectedPackets"],
            "lostPackets": loss["lostPackets"],
            "packetLossPct": loss["packetLossPct"],
            "avgBitrateKbps": round(bitrate_kbps, 6),
            "avgJitterMs": jitter["avgJitterMs"],
            "p50JitterMs": jitter["p50JitterMs"],
            "p95JitterMs": jitter["p95JitterMs"],
            "maxJitterMs": jitter["maxJitterMs"],
            "medianArrivalGapMs": jitter["medianArrivalGapMs"],
            "ignoredReorderOrWrapEvents": loss["ignoredReorderOrWrapEvents"],
            "status": "measured_from_packet_events",
        }

    packet_loss = summary.get("packetLoss", {})
    jitter = summary.get("jitter", {})

    return {
        "mode": mode,
        "receivedPackets": int(summary.get("receivedPackets", 0)),
        "expectedPackets": int(packet_loss.get("expected_packets", 0)),
        "lostPackets": int(packet_loss.get("lost_packets", 0)),
        "packetLossPct": float(packet_loss.get("packet_loss_pct", 100.0)),
        "avgBitrateKbps": float(summary.get("avgBitrateKbps", 0.0)),
        "avgJitterMs": float(jitter.get("avgJitterComponentMs", 0.0)),
        "p50JitterMs": float(jitter.get("p50JitterComponentMs", 0.0)),
        "p95JitterMs": 0.0,
        "maxJitterMs": float(jitter.get("maxJitterComponentMs", 0.0)),
        "medianArrivalGapMs": 0.0,
        "ignoredReorderOrWrapEvents": 0,
        "status": "measured_from_summary",
    }


def copy_artifacts(profile_name, mode, src_summary, src_events):
    if src_summary.exists():
        shutil.copy2(src_summary, OUT_DIR / f"{profile_name}_{mode}_summary.json")

    if src_events.exists():
        shutil.copy2(src_events, OUT_DIR / f"{profile_name}_{mode}_packet_events.csv")


def run_mode(profile_name, mode):
    if mode == "plain_rtp":
        run_cmd(["python", str(PLAIN_SCRIPT)])
        summary = load_json(PLAIN_SUMMARY)
        metrics = extract_metrics(summary, mode, PLAIN_EVENTS)
        copy_artifacts(profile_name, mode, PLAIN_SUMMARY, PLAIN_EVENTS)
        return metrics

    if mode == "dtls_rtp":
        run_cmd(["./dtls_rtp/build.sh"])
        run_cmd(["python", str(DTLS_SCRIPT)])
        summary = load_json(DTLS_SUMMARY)
        metrics = extract_metrics(summary, mode, DTLS_EVENTS)
        copy_artifacts(profile_name, mode, DTLS_SUMMARY, DTLS_EVENTS)
        return metrics

    raise ValueError(mode)


def write_csv(rows):
    fieldnames = [
        "profile",
        "description",
        "mode",
        "receivedPackets",
        "expectedPackets",
        "lostPackets",
        "packetLossPct",
        "avgBitrateKbps",
        "avgJitterMs",
        "p50JitterMs",
        "p95JitterMs",
        "maxJitterMs",
        "medianArrivalGapMs",
        "ignoredReorderOrWrapEvents",
        "status",
    ]

    with SUMMARY_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_md(rows):
    lines = [
        "# Step 91 Network Impairment: Plain RTP vs DTLS-Wrapped RTP",
        "",
        "## Purpose",
        "",
        "This experiment compares plain RTP and DTLS-wrapped RTP media-plane behaviour under controlled loopback impairment using Linux `tc netem`.",
        "",
        "## Important Measurement Note",
        "",
        "The Step 91 matrix computes jitter from packet arrival-gap variation. This avoids misleading raw RTP timestamp artefacts from H.264 packet ordering.",
        "",
        "## Results",
        "",
        "| Profile | Mode | Packets | Loss % | Bitrate kbps | Avg jitter ms | P50 jitter ms | P95 jitter ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for r in rows:
        lines.append(
            f"| {r['profile']} | {r['mode']} | {r['receivedPackets']} | "
            f"{r['packetLossPct']} | {r['avgBitrateKbps']} | {r['avgJitterMs']} | "
            f"{r['p50JitterMs']} | {r['p95JitterMs']} |"
        )

    lines += [
        "",
        "## Research Meaning",
        "",
        "Step 91 extends clean RTP and DTLS/RTP media-plane validation by introducing delay, jitter, and packet-loss impairment.",
        "This strengthens the journal evaluation because it compares plain and secured media delivery under controlled network stress.",
        "",
        "## Boundary",
        "",
        "This remains a localhost loopback impairment experiment. The next stage should reproduce the same setup across two machines, Linux network namespaces, Mininet, or ns-3.",
        "",
    ]

    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def make_bar_figure(rows, metric, ylabel, output):
    profiles = [p["name"] for p in PROFILES]
    plain = []
    dtls = []

    for profile in profiles:
        plain_row = next(r for r in rows if r["profile"] == profile and r["mode"] == "plain_rtp")
        dtls_row = next(r for r in rows if r["profile"] == profile and r["mode"] == "dtls_rtp")
        plain.append(float(plain_row[metric]))
        dtls.append(float(dtls_row[metric]))

    x = list(range(len(profiles)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - width / 2 for i in x], plain, width, label="Plain RTP")
    ax.bar([i + width / 2 for i in x], dtls, width, label="DTLS-wrapped RTP")
    ax.set_xticks(x)
    ax.set_xticklabels(profiles, rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel + " under controlled impairment")
    ax.legend()
    fig.tight_layout()

    fig.savefig(output)
    fig.savefig(output.with_suffix(".pdf"))
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def main():
    print("[preflight] requesting sudo once for tc/netem")
    run_cmd(["sudo", "-v"])

    rows = []

    try:
        for profile in PROFILES:
            apply_profile(profile)
            time.sleep(1)

            for mode in ["plain_rtp", "dtls_rtp"]:
                print(f"\n=== Running {mode} under {profile['name']} ===")
                metrics = run_mode(profile["name"], mode)
                metrics["profile"] = profile["name"]
                metrics["description"] = profile["description"]
                rows.append(metrics)

    finally:
        print("[cleanup] resetting loopback netem")
        reset_netem()

    output = {
        "experiment": "step91_network_impairment_plain_vs_dtls",
        "measurementNote": "Jitter is recomputed from packet arrival-gap variation to avoid raw RTP timestamp artefacts.",
        "profiles": PROFILES,
        "rows": rows,
        "files": {
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryCsv": str(SUMMARY_CSV.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "packetLossFigure": str(FIG_LOSS.relative_to(ROOT)),
            "bitrateFigure": str(FIG_BITRATE.relative_to(ROOT)),
            "jitterFigure": str(FIG_JITTER.relative_to(ROOT)),
        },
    }

    SUMMARY_JSON.write_text(json.dumps(output, indent=2) + "\n")
    write_csv(rows)
    write_md(rows)

    make_bar_figure(rows, "packetLossPct", "Packet loss (%)", FIG_LOSS)
    make_bar_figure(rows, "avgBitrateKbps", "Average bitrate (kbps)", FIG_BITRATE)
    make_bar_figure(rows, "avgJitterMs", "Average arrival-gap jitter (ms)", FIG_JITTER)

    print(json.dumps(output, indent=2))
    print(f"Saved: {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
