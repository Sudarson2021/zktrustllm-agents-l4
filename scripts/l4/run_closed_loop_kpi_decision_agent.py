#!/usr/bin/env python3

"""
Step 97: Closed-Loop KPI Decision Agent for ZKTrustLLM-Agents L4.

Purpose:
- Read current Level 4 KPI/result summaries.
- Validate control-plane, agent-scaling, RTP, DTLS-RTP, impairment, and namespace evidence.
- Produce a machine-readable decision plan.
- Recommend the next safe workflow action without automatically making irreversible changes.

This is a human-approved closed-loop decision layer. It does not push code,
change Git history, submit papers, deploy systems, or run privileged commands automatically.
"""

import json
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_closed_loop_agent"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DECISION_JSON = OUT_DIR / "closed_loop_kpi_decision.json"
DECISION_MD = OUT_DIR / "closed_loop_kpi_decision.md"
DECISION_CSV = OUT_DIR / "closed_loop_kpi_checks.csv"

FILES = {
    "mcp_tool_test": ROOT / "results/l4_mcp_server/mcp_tool_test_results.json",
    "semi_live_control": ROOT / "results/l4_live_telemetry/semi_live_control_summary.json",
    "multi_agent_scaling": ROOT / "results/l4_multi_agent_scaling/multi_agent_scaling_summary.json",
    "plain_rtp": ROOT / "results/l4_live_rtp_media/rtp_media_summary.json",
    "dtls_rtp": ROOT / "results/l4_dtls_rtp_media/dtls_rtp_media_summary.json",
    "loopback_impairment": ROOT / "results/l4_network_impairment/network_impairment_summary.json",
    "namespace_impairment": ROOT / "results/l4_namespace_impairment/namespace_impairment_summary.json",
    "agentic_automation": ROOT / "results/l4_agentic_automation/agentic_automation_summary.json",
}

THRESHOLDS = {
    "plain_rtp_max_loss_pct": 5.0,
    "dtls_rtp_max_loss_pct": 5.0,
    "clean_media_max_jitter_ms": 1000.0,
    "impairment_max_jitter_ms": 1000.0,
    "min_received_packets": 1,
    "min_rows": 1,
}


def load_json(path):
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text()), "valid"
    except Exception as exc:
        return None, f"invalid_json: {exc}"


def nested_get(data, keys, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def status(pass_bool):
    return "PASS" if pass_bool else "FAIL"


def add_check(checks, component, check_name, observed, expected, passed, recommendation):
    checks.append({
        "component": component,
        "check": check_name,
        "observed": observed,
        "expected": expected,
        "status": status(passed),
        "recommendation": recommendation,
    })


def validate_basic_json(name, path, checks):
    data, json_status = load_json(path)
    passed = data is not None
    add_check(
        checks,
        name,
        "json_available_and_valid",
        json_status,
        "valid",
        passed,
        "Regenerate this artifact if missing or invalid.",
    )
    return data, passed


def validate_plain_or_dtls_media(name, data, checks, max_loss_pct):
    if data is None:
        return False

    packets = int(data.get("receivedPackets", 0) or 0)
    bitrate = float(data.get("avgBitrateKbps", 0.0) or 0.0)
    loss = float(nested_get(data, ["packetLoss", "packet_loss_pct"], 100.0) or 100.0)
    jitter = float(nested_get(data, ["jitter", "avgJitterComponentMs"], 0.0) or 0.0)

    ok_packets = packets >= THRESHOLDS["min_received_packets"]
    ok_bitrate = bitrate > 0
    ok_loss = loss <= max_loss_pct
    ok_jitter = jitter <= THRESHOLDS["clean_media_max_jitter_ms"]

    add_check(checks, name, "received_packets_positive", packets, f">= {THRESHOLDS['min_received_packets']}", ok_packets, f"Rerun {name} telemetry.")
    add_check(checks, name, "bitrate_positive", bitrate, "> 0", ok_bitrate, f"Rerun {name} telemetry and inspect sender/receiver logs.")
    add_check(checks, name, "packet_loss_reasonable", loss, f"<= {max_loss_pct}", ok_loss, f"Rerun {name}; inspect RTP sequence or impairment state.")
    add_check(checks, name, "jitter_reasonable", jitter, f"<= {THRESHOLDS['clean_media_max_jitter_ms']}", ok_jitter, f"Recompute arrival-gap jitter or rerun {name} clean baseline.")

    return ok_packets and ok_bitrate and ok_loss and ok_jitter


def validate_matrix(name, data, checks):
    if data is None:
        return False

    rows = data.get("rows", [])
    ok_rows = isinstance(rows, list) and len(rows) >= THRESHOLDS["min_rows"]
    add_check(checks, name, "has_rows", len(rows) if isinstance(rows, list) else "not_list", f">= {THRESHOLDS['min_rows']}", ok_rows, f"Rerun {name} matrix.")

    if not ok_rows:
        return False

    all_ok = True

    for i, row in enumerate(rows):
        packets = int(row.get("receivedPackets", 0) or 0)
        bitrate = float(row.get("avgBitrateKbps", 0.0) or 0.0)
        jitter = float(row.get("avgJitterMs", 0.0) or 0.0)

        ok_packets = packets >= THRESHOLDS["min_received_packets"]
        ok_bitrate = bitrate > 0
        ok_jitter = jitter <= THRESHOLDS["impairment_max_jitter_ms"]

        add_check(checks, name, f"row_{i}_packets_positive", packets, f">= {THRESHOLDS['min_received_packets']}", ok_packets, f"Inspect row {i} receiver logs.")
        add_check(checks, name, f"row_{i}_bitrate_positive", bitrate, "> 0", ok_bitrate, f"Inspect row {i} sender/receiver logs.")
        add_check(checks, name, f"row_{i}_jitter_reasonable", jitter, f"<= {THRESHOLDS['impairment_max_jitter_ms']}", ok_jitter, f"Inspect row {i}; recompute arrival-gap jitter if needed.")

        all_ok = all_ok and ok_packets and ok_bitrate and ok_jitter

    return all_ok


def validate_automation(data, checks):
    if data is None:
        return False

    overall = data.get("overallStatus", "UNKNOWN")
    ok = overall == "PASS"
    add_check(
        checks,
        "agentic_automation",
        "overall_status",
        overall,
        "PASS",
        ok,
        "Rerun Step 96 automation suite or inspect failed validation rows.",
    )
    return ok


def choose_decision(component_status):
    failed = [name for name, ok in component_status.items() if not ok]

    if not failed:
        return {
            "primaryAction": "GENERATE_SUPERVISOR_REPORT",
            "priority": "LOW",
            "humanApprovalRequired": True,
            "reason": "All checked L4 control-plane, media-plane, impairment, namespace, and automation evidence passed.",
            "recommendedCommand": "python scripts/l4/build_l4_full_technical_documentation_steps77_93_pdf.py",
            "nextResearchStep": "Proceed to Step 98: closed-loop remediation executor with dry-run and human approval gates.",
        }

    if "mcp_tool_test" in failed:
        return {
            "primaryAction": "RERUN_MCP_TOOL_VALIDATION",
            "priority": "HIGH",
            "humanApprovalRequired": False,
            "reason": "MCP tool validation is missing or failed. Control-plane evidence must be repaired first.",
            "recommendedCommand": "python scripts/l4/test_mcp_l4_server.py",
            "nextResearchStep": "Repair MCP context retrieval and rerun Step 96 after MCP passes.",
        }

    if "semi_live_control" in failed:
        return {
            "primaryAction": "RERUN_CONTROL_TELEMETRY",
            "priority": "HIGH",
            "humanApprovalRequired": False,
            "reason": "Semi-live control-plane telemetry is missing or failed.",
            "recommendedCommand": "python scripts/l4/run_l4_semi_live_control_telemetry.py",
            "nextResearchStep": "Verify MCP/A2A response time, p50, p95, jitter, and control-message bytes.",
        }

    if "multi_agent_scaling" in failed:
        return {
            "primaryAction": "RERUN_MULTI_AGENT_SCALING",
            "priority": "HIGH",
            "humanApprovalRequired": False,
            "reason": "Multi-agent scaling telemetry is missing or failed.",
            "recommendedCommand": "python scripts/l4/run_l4_multi_agent_scaling_telemetry.py",
            "nextResearchStep": "Verify scaling from 5 to 25 agents and compare L4-ref with raw-context coordination.",
        }

    if "plain_rtp" in failed:
        return {
            "primaryAction": "RERUN_CLEAN_RTP_BASELINE",
            "priority": "HIGH",
            "humanApprovalRequired": False,
            "reason": "Clean RTP baseline is missing, invalid, or outside KPI thresholds.",
            "recommendedCommand": "python scripts/l4/run_live_rtp_media_telemetry.py",
            "nextResearchStep": "Repair plain RTP telemetry before interpreting DTLS or impaired media-plane results.",
        }

    if "dtls_rtp" in failed:
        return {
            "primaryAction": "RERUN_DTLS_RTP_VALIDATION",
            "priority": "HIGH",
            "humanApprovalRequired": False,
            "reason": "DTLS-wrapped RTP validation is missing, invalid, or outside KPI thresholds.",
            "recommendedCommand": "./dtls_rtp/build.sh && python scripts/l4/run_dtls_rtp_media_telemetry.py && python scripts/l4/recompute_dtls_rtp_arrival_jitter.py",
            "nextResearchStep": "Repair secured media-plane baseline before impairment automation.",
        }

    if "loopback_impairment" in failed:
        return {
            "primaryAction": "RERUN_LOOPBACK_IMPAIRMENT_MATRIX",
            "priority": "MEDIUM",
            "humanApprovalRequired": True,
            "reason": "Loopback impairment matrix is missing or failed. This uses tc/netem and may need sudo.",
            "recommendedCommand": "sudo -v && python scripts/l4/run_step91_network_impairment_matrix.py",
            "nextResearchStep": "Validate delay, jitter, and packet-loss stress behaviour on localhost loopback.",
        }

    if "namespace_impairment" in failed:
        return {
            "primaryAction": "RERUN_NAMESPACE_IMPAIRMENT_MATRIX",
            "priority": "MEDIUM",
            "humanApprovalRequired": True,
            "reason": "Namespace impairment matrix is missing or failed. This uses network namespaces and sudo.",
            "recommendedCommand": "sudo -v && python scripts/l4/run_step93_namespace_impairment_matrix.py",
            "nextResearchStep": "Validate plain RTP vs DTLS-RTP in isolated sender/receiver namespaces.",
        }

    if "agentic_automation" in failed:
        return {
            "primaryAction": "RERUN_FULL_AGENTIC_AUTOMATION",
            "priority": "MEDIUM",
            "humanApprovalRequired": True,
            "reason": "The Step 96 full automation summary is missing or not PASS.",
            "recommendedCommand": "sudo -v && python scripts/l4/run_l4_agentic_automation_suite.py --include-privileged",
            "nextResearchStep": "Use the full automation suite as the supervisor-ready evidence generator.",
        }

    return {
        "primaryAction": "REVIEW_REQUIRED",
        "priority": "MEDIUM",
        "humanApprovalRequired": True,
        "reason": f"Some components failed and need manual review: {', '.join(failed)}",
        "recommendedCommand": "sed -n '1,240p' results/l4_closed_loop_agent/closed_loop_kpi_decision.md",
        "nextResearchStep": "Inspect failed KPI rows and decide whether to rerun targeted or full automation.",
    }


def write_csv(checks):
    with DECISION_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["component", "check", "observed", "expected", "status", "recommendation"],
        )
        writer.writeheader()
        writer.writerows(checks)


def write_markdown(result):
    lines = []
    lines.append("# Step 97 Closed-Loop KPI Decision Agent")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("This report is generated by the Step 97 decision agent. It reads current Level 4 KPI artifacts and recommends the next safe workflow action.")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    d = result["decision"]
    lines.append(f"- Primary action: `{d['primaryAction']}`")
    lines.append(f"- Priority: `{d['priority']}`")
    lines.append(f"- Human approval required: `{d['humanApprovalRequired']}`")
    lines.append(f"- Reason: {d['reason']}")
    lines.append(f"- Recommended command: `{d['recommendedCommand']}`")
    lines.append(f"- Next research step: {d['nextResearchStep']}")
    lines.append("")
    lines.append("## Component Status")
    lines.append("")
    lines.append("| Component | Status |")
    lines.append("|---|---:|")
    for comp, ok in result["componentStatus"].items():
        lines.append(f"| {comp} | {'PASS' if ok else 'FAIL'} |")
    lines.append("")
    lines.append("## KPI Checks")
    lines.append("")
    lines.append("| Component | Check | Observed | Expected | Status | Recommendation |")
    lines.append("|---|---|---:|---:|---:|---|")
    for c in result["checks"]:
        lines.append(
            f"| {c['component']} | {c['check']} | {c['observed']} | {c['expected']} | {c['status']} | {c['recommendation']} |"
        )
    lines.append("")
    lines.append("## Human-in-the-Loop Boundary")
    lines.append("")
    lines.append("This decision agent does not automatically push code, deploy systems, run privileged commands, submit papers, or make irreversible research decisions. It recommends the next action for human approval.")
    lines.append("")
    lines.append("## Generated Files")
    lines.append("")
    lines.append(f"- JSON: `{DECISION_JSON.relative_to(ROOT)}`")
    lines.append(f"- Markdown: `{DECISION_MD.relative_to(ROOT)}`")
    lines.append(f"- CSV: `{DECISION_CSV.relative_to(ROOT)}`")
    lines.append("")
    DECISION_MD.write_text("\n".join(lines))


def main():
    checks = []
    component_status = {}

    mcp, ok_json = validate_basic_json("mcp_tool_test", FILES["mcp_tool_test"], checks)
    component_status["mcp_tool_test"] = ok_json

    semi, ok_json = validate_basic_json("semi_live_control", FILES["semi_live_control"], checks)
    component_status["semi_live_control"] = ok_json

    scaling, ok_json = validate_basic_json("multi_agent_scaling", FILES["multi_agent_scaling"], checks)
    component_status["multi_agent_scaling"] = ok_json

    plain, ok_json = validate_basic_json("plain_rtp", FILES["plain_rtp"], checks)
    component_status["plain_rtp"] = ok_json and validate_plain_or_dtls_media(
        "plain_rtp",
        plain,
        checks,
        THRESHOLDS["plain_rtp_max_loss_pct"],
    )

    dtls, ok_json = validate_basic_json("dtls_rtp", FILES["dtls_rtp"], checks)
    component_status["dtls_rtp"] = ok_json and validate_plain_or_dtls_media(
        "dtls_rtp",
        dtls,
        checks,
        THRESHOLDS["dtls_rtp_max_loss_pct"],
    )

    loopback, ok_json = validate_basic_json("loopback_impairment", FILES["loopback_impairment"], checks)
    component_status["loopback_impairment"] = ok_json and validate_matrix("loopback_impairment", loopback, checks)

    namespace, ok_json = validate_basic_json("namespace_impairment", FILES["namespace_impairment"], checks)
    component_status["namespace_impairment"] = ok_json and validate_matrix("namespace_impairment", namespace, checks)

    automation, ok_json = validate_basic_json("agentic_automation", FILES["agentic_automation"], checks)
    component_status["agentic_automation"] = ok_json and validate_automation(automation, checks)

    decision = choose_decision(component_status)

    result = {
        "experiment": "step97_closed_loop_kpi_decision_agent",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "thresholds": THRESHOLDS,
        "componentStatus": component_status,
        "decision": decision,
        "checks": checks,
        "files": {
            "decisionJson": str(DECISION_JSON.relative_to(ROOT)),
            "decisionMarkdown": str(DECISION_MD.relative_to(ROOT)),
            "decisionCsv": str(DECISION_CSV.relative_to(ROOT)),
        },
    }

    DECISION_JSON.write_text(json.dumps(result, indent=2))
    write_csv(checks)
    write_markdown(result)

    print(json.dumps({
        "experiment": result["experiment"],
        "primaryAction": decision["primaryAction"],
        "priority": decision["priority"],
        "humanApprovalRequired": decision["humanApprovalRequired"],
        "decisionJson": result["files"]["decisionJson"],
        "decisionMarkdown": result["files"]["decisionMarkdown"],
        "decisionCsv": result["files"]["decisionCsv"],
    }, indent=2))


if __name__ == "__main__":
    main()
