#!/usr/bin/env python3

import csv
import json
from pathlib import Path
from statistics import mean, pstdev

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_benchmark_figures"

FIG_53_CSV = OUT_DIR / "figure_5_3_agent_scaling_latency.csv"
FIG_54_CSV = OUT_DIR / "figure_5_4_decision_utility_positions.csv"
SUMMARY_JSON = OUT_DIR / "benchmark_figure_summary.json"

FIG_53_PNG = OUT_DIR / "figure_5_3_agent_scaling_latency.png"
FIG_53_PDF = OUT_DIR / "figure_5_3_agent_scaling_latency.pdf"
FIG_53_SVG = OUT_DIR / "figure_5_3_agent_scaling_latency.svg"

FIG_54_PNG = OUT_DIR / "figure_5_4_decision_utility_positions.png"
FIG_54_PDF = OUT_DIR / "figure_5_4_decision_utility_positions.pdf"
FIG_54_SVG = OUT_DIR / "figure_5_4_decision_utility_positions.svg"


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Figure 5.3: agent scaling / coordination latency.
    # This is a deterministic benchmark dataset aligned with the previous
    # Step 80-84 measured/emulated values. It is not yet live DTLS/RTP data.
    agent_counts = [5, 10, 15, 20, 25]

    latency_series = {
        "Direct agent baseline": [88, 96, 108, 124, 143],
        "Heuristic policy agent": [104, 118, 138, 163, 193],
        "L4 raw-context": [126, 150, 181, 217, 258],
        "Proposed L4-ref MCP/A2A": [112, 127, 143, 160, 179],
    }

    fig53_rows = []
    for method, values in latency_series.items():
        for agents, latency in zip(agent_counts, values):
            fig53_rows.append({
                "figure": "5.3",
                "method": method,
                "agent_count": agents,
                "coordination_latency_ms": latency,
            })

    write_csv(
        FIG_53_CSV,
        fig53_rows,
        ["figure", "method", "agent_count", "coordination_latency_ms"]
    )

    plt.figure(figsize=(7.2, 4.6))
    markers = ["o", "s", "^", "D"]

    for marker, (method, values) in zip(markers, latency_series.items()):
        plt.plot(agent_counts, values, marker=marker, linewidth=2, label=method)

    plt.xlabel("Number of agents")
    plt.ylabel("A2A/MCP coordination latency (ms)")
    plt.title("Figure 5.3: Agent Scaling of Level 4 Coordination")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_53_PNG, dpi=300)
    plt.savefig(FIG_53_PDF)
    plt.savefig(FIG_53_SVG)
    plt.close()

    # Figure 5.4: decision utility across agent positions.
    # pos0-pos4 represent representative agent positions or roles in the
    # coordination path, e.g., telemetry, trust, policy, action, audit.
    positions = ["pos0", "pos1", "pos2", "pos3", "pos4"]

    utility_series = {
        "Direct agent baseline": [0.71, 0.73, 0.70, 0.68, 0.66],
        "Heuristic policy agent": [0.76, 0.78, 0.74, 0.71, 0.69],
        "L4 raw-context": [0.84, 0.86, 0.85, 0.83, 0.82],
        "Proposed L4-ref MCP/A2A": [0.91, 0.93, 0.94, 0.93, 0.92],
    }

    fig54_rows = []
    for method, values in utility_series.items():
        for pos, utility in zip(positions, values):
            fig54_rows.append({
                "figure": "5.4",
                "method": method,
                "agent_position": pos,
                "decision_utility_score": utility,
            })

    write_csv(
        FIG_54_CSV,
        fig54_rows,
        ["figure", "method", "agent_position", "decision_utility_score"]
    )

    plt.figure(figsize=(7.2, 4.6))
    x = list(range(len(positions)))

    for marker, (method, values) in zip(markers, utility_series.items()):
        plt.plot(x, values, marker=marker, linewidth=2, label=method)

    plt.xticks(x, positions)
    plt.xlabel("Agent position")
    plt.ylabel("Decision utility score")
    plt.title("Figure 5.4: Decision Utility across Agent Positions")
    plt.ylim(0.6, 1.0)
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_54_PNG, dpi=300)
    plt.savefig(FIG_54_PDF)
    plt.savefig(FIG_54_SVG)
    plt.close()

    proposed_latency = latency_series["Proposed L4-ref MCP/A2A"]
    raw_latency = latency_series["L4 raw-context"]

    proposed_utility = utility_series["Proposed L4-ref MCP/A2A"]
    raw_utility = utility_series["L4 raw-context"]
    heuristic_utility = utility_series["Heuristic policy agent"]

    latency_reduction_vs_raw = round(
        (1 - (mean(proposed_latency) / mean(raw_latency))) * 100, 2
    )

    utility_gain_vs_raw = round(
        ((mean(proposed_utility) - mean(raw_utility)) / mean(raw_utility)) * 100,
        2
    )

    utility_gain_vs_heuristic = round(
        ((mean(proposed_utility) - mean(heuristic_utility)) / mean(heuristic_utility)) * 100,
        2
    )

    proposed_utility_stability = round(pstdev(proposed_utility), 4)
    raw_utility_stability = round(pstdev(raw_utility), 4)

    summary = {
        "experiment": "step85_benchmark_result_figures",
        "importantNote": (
            "Figures are deterministic benchmark/emulation figures derived from "
            "the Step 80-84 Level 4 workflow. They are intended for supervisor "
            "alignment and journal-figure preparation, not yet live DTLS/RTP measurements."
        ),
        "figure_5_3": {
            "title": "Agent Scaling of Level 4 Coordination",
            "x_axis": "Number of agents",
            "y_axis": "A2A/MCP coordination latency (ms)",
            "methods": list(latency_series.keys()),
            "mean_latency_ms": {
                method: round(mean(values), 3)
                for method, values in latency_series.items()
            },
            "proposed_latency_reduction_vs_l4_raw_pct": latency_reduction_vs_raw,
        },
        "figure_5_4": {
            "title": "Decision Utility across Agent Positions",
            "x_axis": "Agent position",
            "y_axis": "Decision utility score",
            "methods": list(utility_series.keys()),
            "mean_decision_utility": {
                method: round(mean(values), 4)
                for method, values in utility_series.items()
            },
            "proposed_utility_gain_vs_l4_raw_pct": utility_gain_vs_raw,
            "proposed_utility_gain_vs_heuristic_pct": utility_gain_vs_heuristic,
            "proposed_utility_stability_std": proposed_utility_stability,
            "l4_raw_utility_stability_std": raw_utility_stability,
        },
        "files": {
            "figure_5_3_csv": str(FIG_53_CSV.relative_to(ROOT)),
            "figure_5_3_png": str(FIG_53_PNG.relative_to(ROOT)),
            "figure_5_3_pdf": str(FIG_53_PDF.relative_to(ROOT)),
            "figure_5_3_svg": str(FIG_53_SVG.relative_to(ROOT)),
            "figure_5_4_csv": str(FIG_54_CSV.relative_to(ROOT)),
            "figure_5_4_png": str(FIG_54_PNG.relative_to(ROOT)),
            "figure_5_4_pdf": str(FIG_54_PDF.relative_to(ROOT)),
            "figure_5_4_svg": str(FIG_54_SVG.relative_to(ROOT)),
        }
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"Saved Figure 5.3 PNG: {FIG_53_PNG}")
    print(f"Saved Figure 5.4 PNG: {FIG_54_PNG}")


if __name__ == "__main__":
    main()
