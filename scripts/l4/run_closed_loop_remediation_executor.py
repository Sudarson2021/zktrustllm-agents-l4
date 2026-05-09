#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION_JSON = ROOT / "results/l4_closed_loop_agent/closed_loop_kpi_decision.json"

OUT_DIR = ROOT / "results/l4_remediation_executor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PLAN_JSON = OUT_DIR / "remediation_execution_plan.json"
PLAN_MD = OUT_DIR / "remediation_execution_plan.md"
STDOUT_LOG = OUT_DIR / "remediation_execution_stdout.log"
STDERR_LOG = OUT_DIR / "remediation_execution_stderr.log"

ACTIONS = {
    "GENERATE_SUPERVISOR_REPORT": {
        "description": "Generate supervisor-ready Level 4 technical documentation PDF.",
        "cmd": [
            sys.executable,
            "scripts/l4/build_l4_full_technical_documentation_steps77_93_pdf.py",
        ],
        "human": True,
        "privileged": False,
        "outputs": [
            "docs/report/zktrustllm_l4_full_technical_documentation_steps77_93.md",
            "results/l4_report_pdf/zktrustllm_l4_full_technical_documentation_steps77_93.pdf",
        ],
    },
    "RERUN_CLEAN_RTP_BASELINE": {
        "description": "Rerun clean plain RTP media-plane telemetry.",
        "cmd": [sys.executable, "scripts/l4/run_live_rtp_media_telemetry.py"],
        "human": False,
        "privileged": False,
        "outputs": [
            "results/l4_live_rtp_media/rtp_media_summary.json",
            "results/l4_live_rtp_media/rtp_packet_events.csv",
        ],
    },
    "RERUN_DTLS_RTP_BASELINE": {
        "description": "Rebuild and rerun DTLS-wrapped RTP media-plane telemetry.",
        "cmd": [
            "bash",
            "-lc",
            "./dtls_rtp/build.sh && "
            f"{sys.executable} scripts/l4/run_dtls_rtp_media_telemetry.py && "
            f"{sys.executable} scripts/l4/recompute_dtls_rtp_arrival_jitter.py",
        ],
        "human": False,
        "privileged": False,
        "outputs": [
            "results/l4_dtls_rtp_media/dtls_rtp_media_summary.json",
            "results/l4_dtls_rtp_media/dtls_rtp_packet_events.csv",
        ],
    },
    "RERUN_AGENTIC_AUTOMATION_SUITE": {
        "description": "Rerun non-privileged Step 96 automation suite.",
        "cmd": [sys.executable, "scripts/l4/run_l4_agentic_automation_suite.py"],
        "human": False,
        "privileged": False,
        "outputs": [
            "results/l4_agentic_automation/agentic_automation_summary.json",
            "results/l4_agentic_automation/agentic_automation_summary.md",
        ],
    },
    "RERUN_PRIVILEGED_NETWORK_VALIDATION": {
        "description": "Rerun full Step 96 automation suite with privileged network validation.",
        "cmd": [
            sys.executable,
            "scripts/l4/run_l4_agentic_automation_suite.py",
            "--include-privileged",
        ],
        "human": True,
        "privileged": True,
        "outputs": [
            "results/l4_agentic_automation/agentic_automation_summary.json",
            "results/l4_network_impairment/network_impairment_summary.json",
            "results/l4_namespace_impairment/namespace_impairment_summary.json",
        ],
    },
}

def rel(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except Exception:
        return str(path)


def read_decision():
    if not DECISION_JSON.exists():
        raise SystemExit(f"Missing Step 97 decision file: {DECISION_JSON}")

    raw = json.loads(DECISION_JSON.read_text())
    nested = raw.get("decision", {}) if isinstance(raw.get("decision"), dict) else {}

    return {
        **raw,
        "primaryAction": raw.get("primaryAction") or nested.get("primaryAction"),
        "priority": raw.get("priority") or nested.get("priority"),
        "humanApprovalRequired": (
            raw["humanApprovalRequired"]
            if "humanApprovalRequired" in raw and raw.get("humanApprovalRequired") is not None
            else nested.get("humanApprovalRequired")
        ),
        "reason": raw.get("reason") or nested.get("reason"),
        "recommendedCommand": raw.get("recommendedCommand") or nested.get("recommendedCommand"),
        "nextResearchStep": raw.get("nextResearchStep") or nested.get("nextResearchStep"),
    }


def write_markdown(plan):
    lines = [
        "# Step 98 Closed-Loop Remediation Executor",
        "",
        "## Purpose",
        "",
        "This file records the safe remediation plan generated from the Step 97 closed-loop KPI decision agent.",
        "",
        "## Plan",
        "",
        f"- Run ID: `{plan['runId']}`",
        f"- Mode: `{plan['mode']}`",
        f"- Status: **{plan['status']}**",
        f"- Primary action: `{plan['primaryAction']}`",
        f"- Human approval required: `{plan['humanApprovalRequired']}`",
        f"- Privileged execution required: `{plan['requiresPrivilegedExecution']}`",
        "",
        "## Command",
        "",
        "```bash",
        plan["commandString"],
        "```",
        "",
        "## Reason",
        "",
        plan["reason"],
        "",
        "## Expected Outputs",
        "",
    ]

    for output in plan["expectedOutputs"]:
        lines.append(f"- `{output}`")

    lines += [
        "",
        "## Safety Boundary",
        "",
        "This executor does not automatically push code, deploy systems, submit papers, or make irreversible research decisions.",
        "",
        "Execution requires explicit approval flags.",
        "",
    ]

    PLAN_MD.write_text("\n".join(lines))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approve-human", action="store_true")
    parser.add_argument("--allow-privileged", action="store_true")
    args = parser.parse_args()

    decision = read_decision()
    action = decision.get("primaryAction", "UNKNOWN")
    reason = decision.get("reason", "No Step 97 reason provided.")
    selected = ACTIONS.get(action)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    if selected is None:
        plan = {
            "experiment": "step98_closed_loop_remediation_executor",
            "runId": run_id,
            "mode": "execute" if args.execute else "dry-run",
            "status": "BLOCKED_UNKNOWN_ACTION",
            "primaryAction": action,
            "priority": decision.get("priority", "UNKNOWN"),
            "reason": f"Unknown action `{action}`. Add it to ACTIONS before execution.",
            "description": "Unknown Step 97 action.",
            "humanApprovalRequired": True,
            "requiresPrivilegedExecution": False,
            "command": [],
            "commandString": "",
            "returnCode": None,
            "expectedOutputs": [],
            "sourceDecisionJson": rel(DECISION_JSON),
            "stdoutLog": rel(STDOUT_LOG),
            "stderrLog": rel(STDERR_LOG),
        }

        PLAN_JSON.write_text(json.dumps(plan, indent=2))
        write_markdown(plan)
        print(json.dumps(plan, indent=2))
        raise SystemExit(1)

    cmd = selected["cmd"]
    status = "DRY_RUN_READY"
    return_code = None

    if args.execute:
        if selected["human"] and not args.approve_human:
            status = "BLOCKED_HUMAN_APPROVAL_REQUIRED"
        elif selected["privileged"] and not args.allow_privileged:
            status = "BLOCKED_PRIVILEGED_APPROVAL_REQUIRED"
        else:
            with STDOUT_LOG.open("w") as out, STDERR_LOG.open("w") as err:
                proc = subprocess.run(
                    cmd,
                    cwd=ROOT,
                    stdout=out,
                    stderr=err,
                    text=True,
                )
            return_code = proc.returncode
            status = "EXECUTED_PASS" if proc.returncode == 0 else "EXECUTED_FAIL"

    plan = {
        "experiment": "step98_closed_loop_remediation_executor",
        "runId": run_id,
        "mode": "execute" if args.execute else "dry-run",
        "status": status,
        "primaryAction": action,
        "priority": decision.get("priority", "UNKNOWN"),
        "reason": reason,
        "description": selected["description"],
        "humanApprovalRequired": bool(selected["human"]),
        "requiresPrivilegedExecution": bool(selected["privileged"]),
        "command": cmd,
        "commandString": " ".join(str(x) for x in cmd),
        "returnCode": return_code,
        "expectedOutputs": selected["outputs"],
        "sourceDecisionJson": rel(DECISION_JSON),
        "stdoutLog": rel(STDOUT_LOG),
        "stderrLog": rel(STDERR_LOG),
    }

    PLAN_JSON.write_text(json.dumps(plan, indent=2))
    write_markdown(plan)

    print(json.dumps({
        "experiment": plan["experiment"],
        "runId": run_id,
        "status": status,
        "primaryAction": action,
        "mode": plan["mode"],
        "planJson": rel(PLAN_JSON),
        "planMarkdown": rel(PLAN_MD),
    }, indent=2))

    if status == "EXECUTED_FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
