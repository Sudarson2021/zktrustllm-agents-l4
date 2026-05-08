#!/usr/bin/env python3

import asyncio
import csv
import json
import math
import statistics
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_multi_agent_scaling"

EVENTS_CSV = OUT_DIR / "multi_agent_scaling_events.csv"
SUMMARY_JSON = OUT_DIR / "multi_agent_scaling_summary.json"
SUMMARY_MD = OUT_DIR / "multi_agent_scaling_summary.md"

FIG_LATENCY_PNG = OUT_DIR / "figure_5_7_multi_agent_scaling_latency.png"
FIG_LATENCY_PDF = OUT_DIR / "figure_5_7_multi_agent_scaling_latency.pdf"
FIG_LATENCY_SVG = OUT_DIR / "figure_5_7_multi_agent_scaling_latency.svg"

FIG_BYTES_PNG = OUT_DIR / "figure_5_8_multi_agent_control_bytes.png"
FIG_BYTES_PDF = OUT_DIR / "figure_5_8_multi_agent_control_bytes.pdf"
FIG_BYTES_SVG = OUT_DIR / "figure_5_8_multi_agent_control_bytes.svg"

FIG_THROUGHPUT_PNG = OUT_DIR / "figure_5_9_multi_agent_throughput.png"
FIG_THROUGHPUT_PDF = OUT_DIR / "figure_5_9_multi_agent_throughput.pdf"
FIG_THROUGHPUT_SVG = OUT_DIR / "figure_5_9_multi_agent_throughput.svg"


AGENT_COUNTS = [5, 10, 15, 20, 25]
REPETITIONS = 3


def compact_size(obj) -> int:
    return len(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def extract_text(result):
    if not result.content:
        return ""
    item = result.content[0]
    return getattr(item, "text", str(item))


async def call_tool(session, tool_name, arguments):
    start = time.perf_counter()
    result = await session.call_tool(tool_name, arguments)
    latency_ms = (time.perf_counter() - start) * 1000

    text = extract_text(result)
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {"rawText": text}

    return parsed, latency_ms


def local_direct_agent_batch(agent_count: int, repetition: int):
    start = time.perf_counter()

    messages = []
    for agent_index in range(agent_count):
        messages.append({
            "agentIndex": agent_index,
            "eventType": "trust_state_trigger",
            "trustState": 3,
            "actionClass": 3,
            "localPolicy": "restricted_to_isolate",
            "proofGoverned": False,
            "referenceBound": False,
        })

    accepted = all(m["trustState"] == 3 and m["actionClass"] == 3 for m in messages)
    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "ok": accepted,
        "latencyMs": latency_ms,
        "messageBytes": compact_size(messages),
        "acceptedCount": len(messages) if accepted else 0,
    }


async def l4_raw_context_batch(session, agent_count: int, repetition: int):
    start = time.perf_counter()
    messages = []
    success_count = 0

    for agent_index in range(agent_count):
        decision, _ = await call_tool(session, "get_auth_v2_2_decision", {"decision_id": 1})
        reference, _ = await call_tool(session, "get_a2a_reference", {"reference_id": 1})
        bundle, _ = await call_tool(session, "verify_reference_bundle", {"reference_id": 1})

        ok = (
            decision.get("ok") is True
            and reference.get("ok") is True
            and bundle.get("ok") is True
            and bundle.get("bundleValid") is True
        )

        if ok:
            success_count += 1

        messages.append({
            "agentIndex": agent_index,
            "mode": "l4_raw_context",
            "decision": decision,
            "reference": reference,
            "bundle": bundle,
        })

    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "ok": success_count == agent_count,
        "latencyMs": latency_ms,
        "messageBytes": compact_size(messages),
        "acceptedCount": success_count,
    }


async def l4_ref_mcp_a2a_batch(session, agent_count: int, repetition: int):
    start = time.perf_counter()
    messages = []
    success_count = 0

    for agent_index in range(agent_count):
        reference_message = {
            "agentIndex": agent_index,
            "mode": "l4_ref_mcp_a2a",
            "referenceId": 1,
            "sourceDecisionId": 1,
        }

        bundle, _ = await call_tool(session, "verify_reference_bundle", {"reference_id": 1})
        ok = bundle.get("ok") is True and bundle.get("bundleValid") is True

        if ok:
            success_count += 1

        messages.append(reference_message)

    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "ok": success_count == agent_count,
        "latencyMs": latency_ms,
        "messageBytes": compact_size(messages),
        "acceptedCount": success_count,
    }


def percentile(values, q):
    ordered = sorted(values)
    index = math.ceil(q * len(ordered)) - 1
    index = max(0, min(index, len(ordered) - 1))
    return ordered[index]


def summarise(rows):
    summary = {}
    keys = sorted(set((r["mode"], int(r["agent_count"])) for r in rows))

    for mode, agent_count in keys:
        subset = [r for r in rows if r["mode"] == mode and int(r["agent_count"]) == agent_count]

        latencies = [float(r["total_latency_ms"]) for r in subset]
        per_agent_latencies = [float(r["latency_per_agent_ms"]) for r in subset]
        bytes_values = [int(r["control_message_bytes"]) for r in subset]
        throughput_values = [float(r["agents_per_second"]) for r in subset]
        failures = [r for r in subset if r["success"] != "true"]

        summary_key = f"{mode}_{agent_count}_agents"
        summary[summary_key] = {
            "mode": mode,
            "agentCount": agent_count,
            "repetitions": len(subset),
            "successRate": round((len(subset) - len(failures)) / len(subset), 4),
            "avgTotalLatencyMs": round(statistics.mean(latencies), 3),
            "p50TotalLatencyMs": round(statistics.median(latencies), 3),
            "p95TotalLatencyMs": round(percentile(latencies, 0.95), 3),
            "jitterStdMs": round(statistics.pstdev(latencies), 3),
            "avgLatencyPerAgentMs": round(statistics.mean(per_agent_latencies), 3),
            "avgControlMessageBytes": round(statistics.mean(bytes_values), 3),
            "avgAgentsPerSecond": round(statistics.mean(throughput_values), 3),
        }

    comparisons = {}

    for agent_count in AGENT_COUNTS:
        raw_key = f"l4_raw_context_{agent_count}_agents"
        ref_key = f"l4_ref_mcp_a2a_{agent_count}_agents"

        if raw_key in summary and ref_key in summary:
            raw_latency = summary[raw_key]["avgTotalLatencyMs"]
            ref_latency = summary[ref_key]["avgTotalLatencyMs"]
            raw_bytes = summary[raw_key]["avgControlMessageBytes"]
            ref_bytes = summary[ref_key]["avgControlMessageBytes"]
            raw_throughput = summary[raw_key]["avgAgentsPerSecond"]
            ref_throughput = summary[ref_key]["avgAgentsPerSecond"]

            comparisons[f"{agent_count}_agents"] = {
                "l4RefLatencyReductionVsRawPct": round((1 - (ref_latency / raw_latency)) * 100, 2),
                "l4RefMessageReductionVsRawPct": round((1 - (ref_bytes / raw_bytes)) * 100, 2),
                "l4RefThroughputGainVsRawPct": round(((ref_throughput - raw_throughput) / raw_throughput) * 100, 2),
            }

    return {
        "byScenario": summary,
        "comparisons": comparisons,
    }


def write_outputs(rows, summary):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "repetition",
        "agent_count",
        "mode",
        "success",
        "accepted_agents",
        "total_latency_ms",
        "latency_per_agent_ms",
        "control_message_bytes",
        "agents_per_second",
        "proof_governed",
        "reference_bound",
        "notes",
    ]

    with EVENTS_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = {
        "experiment": "step87_multi_agent_scaling_telemetry",
        "importantNote": (
            "These are repeated semi-live MCP/A2A control-plane scaling measurements. "
            "They measure local MCP tool invocation and coordination timing across increasing agent counts. "
            "They are not yet live VLC/DTLS/RTP media-plane measurements."
        ),
        "agentCounts": AGENT_COUNTS,
        "repetitions": REPETITIONS,
        "summary": summary,
        "files": {
            "eventsCsv": str(EVENTS_CSV.relative_to(ROOT)),
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "figureLatencyPng": str(FIG_LATENCY_PNG.relative_to(ROOT)),
            "figureBytesPng": str(FIG_BYTES_PNG.relative_to(ROOT)),
            "figureThroughputPng": str(FIG_THROUGHPUT_PNG.relative_to(ROOT)),
        }
    }

    SUMMARY_JSON.write_text(json.dumps(output, indent=2) + "\n")

    md = [
        "# Step 87 Multi-Agent Scaling Telemetry Summary",
        "",
        "> These results are repeated semi-live MCP/A2A control-plane measurements across increasing agent counts. They are not yet live VLC/DTLS/RTP media telemetry.",
        "",
        "## Scenario Summary",
        "",
        "| Mode | Agents | Repetitions | Success rate | Avg total latency ms | Avg per-agent latency ms | Avg bytes | Avg agents/s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for key, values in summary["byScenario"].items():
        md.append(
            f"| {values['mode']} | {values['agentCount']} | {values['repetitions']} | "
            f"{values['successRate']} | {values['avgTotalLatencyMs']} | "
            f"{values['avgLatencyPerAgentMs']} | {values['avgControlMessageBytes']} | "
            f"{values['avgAgentsPerSecond']} |"
        )

    md.extend([
        "",
        "## L4 Reference Improvements over L4 Raw-Context",
        "",
        "| Agents | Latency reduction | Message reduction | Throughput gain |",
        "|---:|---:|---:|---:|",
    ])

    for agent_label, values in summary["comparisons"].items():
        md.append(
            f"| {agent_label.replace('_agents', '')} | "
            f"{values['l4RefLatencyReductionVsRawPct']}% | "
            f"{values['l4RefMessageReductionVsRawPct']}% | "
            f"{values['l4RefThroughputGainVsRawPct']}% |"
        )

    md.extend([
        "",
        "## Research Meaning",
        "",
        "The multi-agent scaling telemetry shows how the proposed L4-ref MCP/A2A coordination path behaves as the number of agents increases. It provides measured evidence that compact reference exchange reduces control-message size and improves coordination efficiency compared with raw-context exchange.",
    ])

    SUMMARY_MD.write_text("\n".join(md) + "\n")


def make_figures(summary):
    modes = ["baseline_direct_agent", "l4_raw_context", "l4_ref_mcp_a2a"]
    label_map = {
        "baseline_direct_agent": "Baseline direct",
        "l4_raw_context": "L4 raw-context",
        "l4_ref_mcp_a2a": "Proposed L4-ref",
    }

    plt.figure(figsize=(7.6, 4.8))
    for mode in modes:
        y = [summary["byScenario"][f"{mode}_{agent_count}_agents"]["avgTotalLatencyMs"] for agent_count in AGENT_COUNTS]
        plt.plot(AGENT_COUNTS, y, marker="o", linewidth=2, label=label_map[mode])

    plt.xlabel("Number of agents")
    plt.ylabel("Measured total coordination latency (ms)")
    plt.title("Figure 5.7: Multi-Agent Scaling Latency")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_LATENCY_PNG, dpi=300)
    plt.savefig(FIG_LATENCY_PDF)
    plt.savefig(FIG_LATENCY_SVG)
    plt.close()

    plt.figure(figsize=(7.6, 4.8))
    for mode in modes:
        y = [summary["byScenario"][f"{mode}_{agent_count}_agents"]["avgControlMessageBytes"] for agent_count in AGENT_COUNTS]
        plt.plot(AGENT_COUNTS, y, marker="s", linewidth=2, label=label_map[mode])

    plt.xlabel("Number of agents")
    plt.ylabel("Average control-message bytes")
    plt.title("Figure 5.8: Multi-Agent Control-Message Size")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_BYTES_PNG, dpi=300)
    plt.savefig(FIG_BYTES_PDF)
    plt.savefig(FIG_BYTES_SVG)
    plt.close()

    plt.figure(figsize=(7.6, 4.8))
    for mode in modes:
        y = [summary["byScenario"][f"{mode}_{agent_count}_agents"]["avgAgentsPerSecond"] for agent_count in AGENT_COUNTS]
        plt.plot(AGENT_COUNTS, y, marker="^", linewidth=2, label=label_map[mode])

    plt.xlabel("Number of agents")
    plt.ylabel("Average accepted agents per second")
    plt.title("Figure 5.9: Multi-Agent Coordination Throughput")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_THROUGHPUT_PNG, dpi=300)
    plt.savefig(FIG_THROUGHPUT_PDF)
    plt.savefig(FIG_THROUGHPUT_SVG)
    plt.close()


async def main():
    rows = []

    server_script = ROOT / "mcp_l4" / "server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            preflight, _ = await call_tool(session, "verify_reference_bundle", {"reference_id": 1})
            if preflight.get("ok") is not True or preflight.get("bundleValid") is not True:
                raise RuntimeError("MCP/A2A preflight failed. Refresh A2A reference 1 before running Step 87.")

            for repetition in range(1, REPETITIONS + 1):
                for agent_count in AGENT_COUNTS:
                    baseline = local_direct_agent_batch(agent_count, repetition)
                    rows.append({
                        "repetition": repetition,
                        "agent_count": agent_count,
                        "mode": "baseline_direct_agent",
                        "success": str(baseline["ok"]).lower(),
                        "accepted_agents": baseline["acceptedCount"],
                        "total_latency_ms": round(baseline["latencyMs"], 3),
                        "latency_per_agent_ms": round(baseline["latencyMs"] / agent_count, 3),
                        "control_message_bytes": baseline["messageBytes"],
                        "agents_per_second": round(agent_count / max(baseline["latencyMs"] / 1000, 1e-9), 3),
                        "proof_governed": "false",
                        "reference_bound": "false",
                        "notes": "local direct policy batch",
                    })

                    raw = await l4_raw_context_batch(session, agent_count, repetition)
                    rows.append({
                        "repetition": repetition,
                        "agent_count": agent_count,
                        "mode": "l4_raw_context",
                        "success": str(raw["ok"]).lower(),
                        "accepted_agents": raw["acceptedCount"],
                        "total_latency_ms": round(raw["latencyMs"], 3),
                        "latency_per_agent_ms": round(raw["latencyMs"] / agent_count, 3),
                        "control_message_bytes": raw["messageBytes"],
                        "agents_per_second": round(agent_count / max(raw["latencyMs"] / 1000, 1e-9), 3),
                        "proof_governed": "true",
                        "reference_bound": "false",
                        "notes": "MCP decision+reference+bundle batch",
                    })

                    ref = await l4_ref_mcp_a2a_batch(session, agent_count, repetition)
                    rows.append({
                        "repetition": repetition,
                        "agent_count": agent_count,
                        "mode": "l4_ref_mcp_a2a",
                        "success": str(ref["ok"]).lower(),
                        "accepted_agents": ref["acceptedCount"],
                        "total_latency_ms": round(ref["latencyMs"], 3),
                        "latency_per_agent_ms": round(ref["latencyMs"] / agent_count, 3),
                        "control_message_bytes": ref["messageBytes"],
                        "agents_per_second": round(agent_count / max(ref["latencyMs"] / 1000, 1e-9), 3),
                        "proof_governed": "true",
                        "reference_bound": "true",
                        "notes": "compact A2A reference batch plus MCP bundle verification",
                    })

    summary = summarise(rows)
    write_outputs(rows, summary)
    make_figures(summary)

    print(json.dumps({
        "experiment": "step87_multi_agent_scaling_telemetry",
        "agentCounts": AGENT_COUNTS,
        "repetitions": REPETITIONS,
        "summaryJson": str(SUMMARY_JSON),
        "summaryMarkdown": str(SUMMARY_MD),
        "figure57": str(FIG_LATENCY_PNG),
        "figure58": str(FIG_BYTES_PNG),
        "figure59": str(FIG_THROUGHPUT_PNG),
        "comparisons": summary["comparisons"],
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
