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
OUT_DIR = ROOT / "results" / "l4_live_telemetry"

EVENTS_CSV = OUT_DIR / "semi_live_control_events.csv"
SUMMARY_JSON = OUT_DIR / "semi_live_control_summary.json"
SUMMARY_MD = OUT_DIR / "semi_live_control_summary.md"

FIG_LATENCY_PNG = OUT_DIR / "figure_5_5_semi_live_control_latency.png"
FIG_LATENCY_PDF = OUT_DIR / "figure_5_5_semi_live_control_latency.pdf"
FIG_LATENCY_SVG = OUT_DIR / "figure_5_5_semi_live_control_latency.svg"

FIG_SUMMARY_PNG = OUT_DIR / "figure_5_6_semi_live_control_summary.png"
FIG_SUMMARY_PDF = OUT_DIR / "figure_5_6_semi_live_control_summary.pdf"
FIG_SUMMARY_SVG = OUT_DIR / "figure_5_6_semi_live_control_summary.svg"


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


def local_direct_agent_decision(run_id: int):
    start = time.perf_counter()

    event = {
        "runId": run_id,
        "eventType": "trust_state_trigger",
        "trustState": 3,
        "actionClass": 3,
        "localPolicy": "restricted_to_isolate",
        "proofGoverned": False,
        "referenceBound": False,
    }

    accepted = event["trustState"] == 3 and event["actionClass"] == 3

    latency_ms = (time.perf_counter() - start) * 1000
    message_bytes = compact_size(event)

    return {
        "ok": accepted,
        "latencyMs": latency_ms,
        "messageBytes": message_bytes,
        "details": event,
    }


async def l4_raw_context_decision(session, run_id: int):
    start = time.perf_counter()

    decision, decision_latency = await call_tool(
        session,
        "get_auth_v2_2_decision",
        {"decision_id": 1}
    )

    reference, reference_latency = await call_tool(
        session,
        "get_a2a_reference",
        {"reference_id": 1}
    )

    bundle, bundle_latency = await call_tool(
        session,
        "verify_reference_bundle",
        {"reference_id": 1}
    )

    total_latency_ms = (time.perf_counter() - start) * 1000

    raw_payload = {
        "runId": run_id,
        "mode": "l4_raw_context",
        "decision": decision,
        "reference": reference,
        "bundle": bundle,
    }

    ok = (
        decision.get("ok") is True
        and reference.get("ok") is True
        and bundle.get("ok") is True
        and bundle.get("bundleValid") is True
    )

    return {
        "ok": ok,
        "latencyMs": total_latency_ms,
        "messageBytes": compact_size(raw_payload),
        "details": {
            "decisionLatencyMs": decision_latency,
            "referenceLatencyMs": reference_latency,
            "bundleLatencyMs": bundle_latency,
            "bundleValid": bundle.get("bundleValid"),
        },
    }


async def l4_ref_mcp_a2a_decision(session, run_id: int):
    start = time.perf_counter()

    # This represents compact A2A message exchange.
    compact_reference_message = {
        "runId": run_id,
        "mode": "l4_ref_mcp_a2a",
        "referenceId": 1,
        "sourceDecisionId": 1,
    }

    bundle, bundle_latency = await call_tool(
        session,
        "verify_reference_bundle",
        {"reference_id": 1}
    )

    total_latency_ms = (time.perf_counter() - start) * 1000

    ok = bundle.get("ok") is True and bundle.get("bundleValid") is True

    return {
        "ok": ok,
        "latencyMs": total_latency_ms,
        "messageBytes": compact_size(compact_reference_message),
        "details": {
            "bundleLatencyMs": bundle_latency,
            "bundleValid": bundle.get("bundleValid"),
            "referenceMessage": compact_reference_message,
        },
    }


def summarise(rows):
    summary = {}

    for mode in sorted(set(r["mode"] for r in rows)):
        subset = [r for r in rows if r["mode"] == mode]
        latencies = [float(r["control_response_ms"]) for r in subset]
        bytes_values = [int(r["control_message_bytes"]) for r in subset]
        failures = [r for r in subset if r["success"] != "true"]

        summary[mode] = {
            "runs": len(subset),
            "successCount": len(subset) - len(failures),
            "failureCount": len(failures),
            "successRate": round((len(subset) - len(failures)) / len(subset), 4),
            "controlFailureRatePct": round((len(failures) / len(subset)) * 100, 4),
            "avgControlResponseMs": round(statistics.mean(latencies), 3),
            "p50ControlResponseMs": round(statistics.median(latencies), 3),
            "p95ControlResponseMs": round(sorted(latencies)[math.ceil(0.95 * len(latencies)) - 1], 3),
            "jitterStdMs": round(statistics.pstdev(latencies), 3),
            "avgControlMessageBytes": round(statistics.mean(bytes_values), 3),
            "minControlMessageBytes": min(bytes_values),
            "maxControlMessageBytes": max(bytes_values),
        }

    if "l4_raw_context" in summary and "l4_ref_mcp_a2a" in summary:
        raw_latency = summary["l4_raw_context"]["avgControlResponseMs"]
        ref_latency = summary["l4_ref_mcp_a2a"]["avgControlResponseMs"]

        raw_bytes = summary["l4_raw_context"]["avgControlMessageBytes"]
        ref_bytes = summary["l4_ref_mcp_a2a"]["avgControlMessageBytes"]

        summary["comparison"] = {
            "l4RefLatencyReductionVsRawPct": round((1 - (ref_latency / raw_latency)) * 100, 2),
            "l4RefMessageReductionVsRawPct": round((1 - (ref_bytes / raw_bytes)) * 100, 2),
        }

    return summary


def write_outputs(rows, summary):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "run_id",
        "mode",
        "success",
        "control_response_ms",
        "control_message_bytes",
        "proof_governed",
        "reference_bound",
        "notes",
    ]

    with EVENTS_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = {
        "experiment": "step86_semi_live_control_plane_telemetry",
        "importantNote": (
            "These results are semi-live MCP/A2A control-plane telemetry measurements. "
            "They measure actual local MCP tool invocation and control-loop timings, "
            "but they are not yet live VLC/DTLS/RTP media telemetry."
        ),
        "summary": summary,
        "files": {
            "eventsCsv": str(EVENTS_CSV.relative_to(ROOT)),
            "summaryJson": str(SUMMARY_JSON.relative_to(ROOT)),
            "summaryMarkdown": str(SUMMARY_MD.relative_to(ROOT)),
            "latencyFigurePng": str(FIG_LATENCY_PNG.relative_to(ROOT)),
            "summaryFigurePng": str(FIG_SUMMARY_PNG.relative_to(ROOT)),
        }
    }

    SUMMARY_JSON.write_text(json.dumps(output, indent=2) + "\n")

    md = [
        "# Step 86 Semi-Live Control-Plane Telemetry Summary",
        "",
        "> These results measure actual local MCP/A2A control-plane timings. They are not yet live VLC/DTLS/RTP media telemetry.",
        "",
        "## Scenario Summary",
        "",
        "| Mode | Runs | Success rate | Avg response ms | P50 ms | P95 ms | Jitter std ms | Avg control bytes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for mode, values in summary.items():
        if mode == "comparison":
            continue
        md.append(
            f"| {mode} | {values['runs']} | {values['successRate']} | "
            f"{values['avgControlResponseMs']} | {values['p50ControlResponseMs']} | "
            f"{values['p95ControlResponseMs']} | {values['jitterStdMs']} | "
            f"{values['avgControlMessageBytes']} |"
        )

    if "comparison" in summary:
        md.extend([
            "",
            "## L4 Reference Mode Improvements",
            "",
            f"- L4-ref latency reduction vs L4 raw-context: {summary['comparison']['l4RefLatencyReductionVsRawPct']}%",
            f"- L4-ref control-message reduction vs L4 raw-context: {summary['comparison']['l4RefMessageReductionVsRawPct']}%",
        ])

    md.extend([
        "",
        "## Research Meaning",
        "",
        "The semi-live telemetry validates the MCP/A2A control-plane path using actual local tool invocation timings. It strengthens the Step 83 deterministic network KPI analysis by replacing part of the emulated values with measured control-loop timings.",
    ])

    SUMMARY_MD.write_text("\n".join(md) + "\n")


def make_figures(rows, summary):
    modes = ["baseline_direct_agent", "l4_raw_context", "l4_ref_mcp_a2a"]
    label_map = {
        "baseline_direct_agent": "Baseline direct",
        "l4_raw_context": "L4 raw-context",
        "l4_ref_mcp_a2a": "Proposed L4-ref",
    }

    plt.figure(figsize=(7.4, 4.6))
    for mode in modes:
        subset = [r for r in rows if r["mode"] == mode]
        x = [int(r["run_id"]) for r in subset]
        y = [float(r["control_response_ms"]) for r in subset]
        plt.plot(x, y, marker="o", linewidth=1.8, label=label_map[mode])

    plt.xlabel("Run index")
    plt.ylabel("Measured control response time (ms)")
    plt.title("Figure 5.5: Semi-Live MCP/A2A Control Response")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_LATENCY_PNG, dpi=300)
    plt.savefig(FIG_LATENCY_PDF)
    plt.savefig(FIG_LATENCY_SVG)
    plt.close()

    plt.figure(figsize=(7.4, 4.6))
    x = list(range(len(modes)))
    avg_latency = [summary[m]["avgControlResponseMs"] for m in modes]
    jitter = [summary[m]["jitterStdMs"] for m in modes]

    width = 0.35
    plt.bar([i - width/2 for i in x], avg_latency, width=width, label="Avg response ms")
    plt.bar([i + width/2 for i in x], jitter, width=width, label="Jitter std ms")
    plt.xticks(x, [label_map[m] for m in modes], rotation=12)
    plt.ylabel("Milliseconds")
    plt.title("Figure 5.6: Semi-Live Control Response and Jitter")
    plt.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_SUMMARY_PNG, dpi=300)
    plt.savefig(FIG_SUMMARY_PDF)
    plt.savefig(FIG_SUMMARY_SVG)
    plt.close()


async def main():
    runs = 20
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

            # Preflight check: make sure reference 1 is valid.
            preflight, _ = await call_tool(session, "verify_reference_bundle", {"reference_id": 1})
            if preflight.get("ok") is not True or preflight.get("bundleValid") is not True:
                raise RuntimeError(
                    "MCP/A2A preflight failed. Redeploy AUTH_V2.2/A2A registry and register reference 1."
                )

            for run_id in range(1, runs + 1):
                baseline = local_direct_agent_decision(run_id)
                rows.append({
                    "run_id": run_id,
                    "mode": "baseline_direct_agent",
                    "success": str(baseline["ok"]).lower(),
                    "control_response_ms": round(baseline["latencyMs"], 3),
                    "control_message_bytes": baseline["messageBytes"],
                    "proof_governed": "false",
                    "reference_bound": "false",
                    "notes": "local direct policy decision only",
                })

                raw = await l4_raw_context_decision(session, run_id)
                rows.append({
                    "run_id": run_id,
                    "mode": "l4_raw_context",
                    "success": str(raw["ok"]).lower(),
                    "control_response_ms": round(raw["latencyMs"], 3),
                    "control_message_bytes": raw["messageBytes"],
                    "proof_governed": "true",
                    "reference_bound": "false",
                    "notes": "MCP decision+reference+bundle retrieval",
                })

                ref = await l4_ref_mcp_a2a_decision(session, run_id)
                rows.append({
                    "run_id": run_id,
                    "mode": "l4_ref_mcp_a2a",
                    "success": str(ref["ok"]).lower(),
                    "control_response_ms": round(ref["latencyMs"], 3),
                    "control_message_bytes": ref["messageBytes"],
                    "proof_governed": "true",
                    "reference_bound": "true",
                    "notes": "compact A2A reference plus MCP bundle verification",
                })

    summary = summarise(rows)
    write_outputs(rows, summary)
    make_figures(rows, summary)

    print(json.dumps({
        "experiment": "step86_semi_live_control_plane_telemetry",
        "summary": summary,
        "eventsCsv": str(EVENTS_CSV),
        "summaryJson": str(SUMMARY_JSON),
        "summaryMarkdown": str(SUMMARY_MD),
        "figure55": str(FIG_LATENCY_PNG),
        "figure56": str(FIG_SUMMARY_PNG),
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
