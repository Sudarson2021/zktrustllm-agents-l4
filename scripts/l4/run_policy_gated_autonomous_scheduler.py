#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

POLICY_JSON = ROOT / "configs/l4_automation_policy.json"
STEP97_SCRIPT = ROOT / "scripts/l4/run_closed_loop_kpi_decision_agent.py"
STEP98_SCRIPT = ROOT / "scripts/l4/run_closed_loop_remediation_executor.py"

STEP97_DECISION_JSON = ROOT / "results/l4_closed_loop_agent/closed_loop_kpi_decision.json"
STEP98_PLAN_JSON = ROOT / "results/l4_remediation_executor/remediation_execution_plan.json"

OUT_DIR = ROOT / "results/l4_policy_scheduler"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "policy_scheduler_summary.json"
SUMMARY_MD = OUT_DIR / "policy_scheduler_summary.md"
ROLLBACK_MD = OUT_DIR / "policy_scheduler_rollback_note.md"

STEP97_STDOUT = OUT_DIR / "step97_scheduler_stdout.log"
STEP97_STDERR = OUT_DIR / "step97_scheduler_stderr.log"
STEP98_DRY_STDOUT = OUT_DIR / "step98_dry_run_stdout.log"
STEP98_DRY_STDERR = OUT_DIR / "step98_dry_run_stderr.log"
STEP98_EXEC_STDOUT = OUT_DIR / "step98_execute_stdout.log"
STEP98_EXEC_STDERR = OUT_DIR / "step98_execute_stderr.log"


def rel(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except Exception:
        return str(path)


def read_json(path):
    if not Path(path).exists():
        raise SystemExit(f"Missing JSON file: {path}")
    return json.loads(Path(path).read_text())


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))


def run_cmd(cmd, stdout_path, stderr_path):
    with open(stdout_path, "w") as out, open(stderr_path, "w") as err:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=out,
            stderr=err,
            text=True,
        )
    return proc.returncode


def get_decision_field(decision_data, key, default=None):
    nested = decision_data.get("decision", {})
    if not isinstance(nested, dict):
        nested = {}
    return decision_data.get(key) or nested.get(key, default)


def classify_action(policy, action):
    automatic = set(policy.get("allowedAutomaticActions", []))
    human = set(policy.get("allowedWithHumanApproval", []))
    privileged = set(policy.get("allowedWithHumanAndPrivilegedApproval", []))
    never = set(policy.get("neverAutomatic", []))

    if action in never:
        return {
            "allowed": False,
            "category": "NEVER_AUTOMATIC",
            "humanRequired": True,
            "privilegedRequired": True,
            "reason": "Action is listed as never automatic in the governance policy.",
        }

    if action in automatic:
        return {
            "allowed": True,
            "category": "AUTOMATIC_SAFE",
            "humanRequired": False,
            "privilegedRequired": False,
            "reason": "Action is allowed automatically by policy.",
        }

    if action in human:
        return {
            "allowed": True,
            "category": "HUMAN_APPROVAL_REQUIRED",
            "humanRequired": True,
            "privilegedRequired": False,
            "reason": "Action requires explicit human approval.",
        }

    if action in privileged:
        return {
            "allowed": True,
            "category": "HUMAN_AND_PRIVILEGED_APPROVAL_REQUIRED",
            "humanRequired": True,
            "privilegedRequired": True,
            "reason": "Action requires human approval and privileged execution approval.",
        }

    return {
        "allowed": False,
        "category": "UNKNOWN_ACTION",
        "humanRequired": True,
        "privilegedRequired": False,
        "reason": "Action is not listed in the automation policy.",
    }


def make_markdown(summary):
    lines = [
        "# Step 100 Policy-Gated Autonomous Scheduler",
        "",
        "## Purpose",
        "",
        "This scheduler connects the Step 97 KPI decision agent and Step 98 remediation executor under an explicit automation governance policy.",
        "",
        "## Scheduler Result",
        "",
        f"- Run ID: `{summary['runId']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Overall status: **{summary['overallStatus']}**",
        f"- Step 97 status: `{summary['step97Status']}`",
        f"- Step 98 dry-run status: `{summary['step98DryRunStatus']}`",
        f"- Step 98 execution status: `{summary['step98ExecutionStatus']}`",
        "",
        "## Policy Decision",
        "",
        f"- Primary action: `{summary['primaryAction']}`",
        f"- Priority: `{summary['priority']}`",
        f"- Policy category: `{summary['policyGate']['category']}`",
        f"- Human approval required: `{summary['policyGate']['humanRequired']}`",
        f"- Privileged approval required: `{summary['policyGate']['privilegedRequired']}`",
        "",
        "## Reason",
        "",
        summary["reason"],
        "",
        "## Safety Boundary",
        "",
        "The scheduler does not push code, modify Git history, submit papers, email supervisors, deploy public systems, or delete research evidence.",
        "",
        "Execution remains policy-gated and approval-gated.",
        "",
        "## Generated Artifacts",
        "",
        f"- Summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- Summary Markdown: `{rel(SUMMARY_MD)}`",
        f"- Rollback note: `{rel(ROLLBACK_MD)}`",
    ]

    return "\n".join(lines) + "\n"


def make_rollback_note(summary):
    lines = [
        "# Step 100 Rollback / Recovery Note",
        "",
        "## Purpose",
        "",
        "This note records how to recover from the latest policy-gated scheduler run.",
        "",
        "## Run",
        "",
        f"- Run ID: `{summary['runId']}`",
        f"- Status: `{summary['overallStatus']}`",
        f"- Primary action: `{summary['primaryAction']}`",
        "",
        "## Recovery Guidance",
        "",
        "This scheduler run does not modify Git history, push code, deploy services, submit papers, or delete evidence.",
        "",
        "If generated reports are not desired, they can be regenerated safely from the existing scripts.",
        "",
        "If experiment outputs were overwritten during an approved remediation, restore known-good tracked outputs using:",
        "",
        "```bash",
        "git restore results/l4_live_rtp_media || true",
        "git restore results/l4_dtls_rtp_media || true",
        "git restore results/l4_live_telemetry || true",
        "git restore results/l4_mcp_server || true",
        "git restore results/l4_multi_agent_scaling || true",
        "git restore results/l4_network_impairment || true",
        "git restore results/l4_namespace_impairment || true",
        "```",
        "",
        "Temporary compiled binaries can be removed using:",
        "",
        "```bash",
        "rm -f dtls_rtp/dtls_rtp_proxy",
        "rm -f abi.json out.r1cs out.wtns",
        "```",
    ]

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Execute Step 98 after dry-run if policy allows.")
    parser.add_argument("--approve-human", action="store_true", help="Human approval gate for execution.")
    parser.add_argument("--allow-privileged", action="store_true", help="Allow privileged actions when policy and human approval permit.")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    policy = read_json(POLICY_JSON)

    step97_cmd = [sys.executable, rel(STEP97_SCRIPT)]
    step97_rc = run_cmd(step97_cmd, STEP97_STDOUT, STEP97_STDERR)

    step97_status = "PASS" if step97_rc == 0 and STEP97_DECISION_JSON.exists() else "FAIL"

    if step97_status != "PASS":
        summary = {
            "experiment": "step100_policy_gated_autonomous_scheduler",
            "runId": run_id,
            "mode": "execute" if args.execute else "dry-run",
            "overallStatus": "FAILED_STEP97",
            "step97Status": step97_status,
            "step98DryRunStatus": "NOT_RUN",
            "step98ExecutionStatus": "NOT_RUN",
            "primaryAction": "UNKNOWN",
            "priority": "UNKNOWN",
            "reason": "Step 97 KPI decision agent failed or did not produce a decision JSON.",
            "policyGate": {
                "allowed": False,
                "category": "STEP97_FAILED",
                "humanRequired": True,
                "privilegedRequired": False,
                "reason": "Step 97 failed.",
            },
            "files": {
                "summaryJson": rel(SUMMARY_JSON),
                "summaryMarkdown": rel(SUMMARY_MD),
                "rollbackNote": rel(ROLLBACK_MD),
                "step97Stdout": rel(STEP97_STDOUT),
                "step97Stderr": rel(STEP97_STDERR),
            },
        }
        write_json(SUMMARY_JSON, summary)
        SUMMARY_MD.write_text(make_markdown(summary))
        ROLLBACK_MD.write_text(make_rollback_note(summary))
        print(json.dumps(summary, indent=2))
        raise SystemExit(1)

    decision_data = read_json(STEP97_DECISION_JSON)

    action = get_decision_field(decision_data, "primaryAction", "UNKNOWN")
    priority = get_decision_field(decision_data, "priority", "UNKNOWN")
    reason = get_decision_field(decision_data, "reason", "No decision reason provided.")

    gate = classify_action(policy, action)

    step98_dry_cmd = [sys.executable, rel(STEP98_SCRIPT)]
    step98_dry_rc = run_cmd(step98_dry_cmd, STEP98_DRY_STDOUT, STEP98_DRY_STDERR)

    step98_dry_status = "PASS" if step98_dry_rc == 0 and STEP98_PLAN_JSON.exists() else "FAIL"

    execution_status = "NOT_REQUESTED"

    if args.execute:
        if not gate["allowed"]:
            execution_status = "BLOCKED_BY_POLICY"
        elif gate["humanRequired"] and not args.approve_human:
            execution_status = "BLOCKED_NEEDS_HUMAN_APPROVAL"
        elif gate["privilegedRequired"] and not args.allow_privileged:
            execution_status = "BLOCKED_NEEDS_PRIVILEGED_APPROVAL"
        elif step98_dry_status != "PASS":
            execution_status = "BLOCKED_DRY_RUN_FAILED"
        else:
            step98_exec_cmd = [sys.executable, rel(STEP98_SCRIPT), "--execute", "--approve-human"]
            if args.allow_privileged:
                step98_exec_cmd.append("--allow-privileged")

            step98_exec_rc = run_cmd(step98_exec_cmd, STEP98_EXEC_STDOUT, STEP98_EXEC_STDERR)
            execution_status = "EXECUTED_PASS" if step98_exec_rc == 0 else "EXECUTED_FAIL"

    if step97_status == "PASS" and step98_dry_status == "PASS":
        if args.execute:
            overall = execution_status
        else:
            overall = "DRY_RUN_READY"
    else:
        overall = "FAILED"

    summary = {
        "experiment": "step100_policy_gated_autonomous_scheduler",
        "runId": run_id,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "mode": "execute" if args.execute else "dry-run",
        "overallStatus": overall,
        "step97Status": step97_status,
        "step98DryRunStatus": step98_dry_status,
        "step98ExecutionStatus": execution_status,
        "primaryAction": action,
        "priority": priority,
        "reason": reason,
        "policyGate": gate,
        "approvalFlags": {
            "execute": args.execute,
            "approveHuman": args.approve_human,
            "allowPrivileged": args.allow_privileged,
        },
        "files": {
            "policyJson": rel(POLICY_JSON),
            "step97DecisionJson": rel(STEP97_DECISION_JSON),
            "step98PlanJson": rel(STEP98_PLAN_JSON),
            "summaryJson": rel(SUMMARY_JSON),
            "summaryMarkdown": rel(SUMMARY_MD),
            "rollbackNote": rel(ROLLBACK_MD),
            "step97Stdout": rel(STEP97_STDOUT),
            "step97Stderr": rel(STEP97_STDERR),
            "step98DryStdout": rel(STEP98_DRY_STDOUT),
            "step98DryStderr": rel(STEP98_DRY_STDERR),
            "step98ExecStdout": rel(STEP98_EXEC_STDOUT),
            "step98ExecStderr": rel(STEP98_EXEC_STDERR),
        },
    }

    write_json(SUMMARY_JSON, summary)
    SUMMARY_MD.write_text(make_markdown(summary))
    ROLLBACK_MD.write_text(make_rollback_note(summary))

    print(json.dumps({
        "experiment": summary["experiment"],
        "runId": summary["runId"],
        "overallStatus": summary["overallStatus"],
        "primaryAction": summary["primaryAction"],
        "policyCategory": summary["policyGate"]["category"],
        "summaryJson": summary["files"]["summaryJson"],
        "summaryMarkdown": summary["files"]["summaryMarkdown"],
        "rollbackNote": summary["files"]["rollbackNote"],
    }, indent=2))

    if overall in {"FAILED", "FAILED_STEP97", "EXECUTED_FAIL"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
