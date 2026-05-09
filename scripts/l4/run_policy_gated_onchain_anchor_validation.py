#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

POLICY_JSON = ROOT / "configs/l4_automation_policy.json"

STEP103_SCRIPT = "scripts/l4/submit_l4_audit_anchor_hardhat.js"
STEP104_SCRIPT = "scripts/l4/test_l4_audit_anchor_registry_negative_security.js"

STEP103_RESULT = ROOT / "results/l4_onchain_anchor/onchain_audit_anchor_result.json"
STEP104_RESULT = ROOT / "results/l4_onchain_anchor_negative/onchain_anchor_negative_security_result.json"

OUT_DIR = ROOT / "results/l4_policy_onchain_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_JSON = OUT_DIR / "policy_onchain_validation_summary.json"
SUMMARY_MD = OUT_DIR / "policy_onchain_validation_summary.md"
STEP103_STDOUT = OUT_DIR / "step103_onchain_anchor_stdout.log"
STEP103_STDERR = OUT_DIR / "step103_onchain_anchor_stderr.log"
STEP104_STDOUT = OUT_DIR / "step104_negative_security_stdout.log"
STEP104_STDERR = OUT_DIR / "step104_negative_security_stderr.log"

ACTION = "VALIDATE_ONCHAIN_AUDIT_ANCHOR_SECURITY"


def rel(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except Exception:
        return str(path)


def read_json(path, default=None):
    if not Path(path).exists():
        return default
    return json.loads(Path(path).read_text())


def run_cmd(cmd, stdout_path, stderr_path):
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    Path(stdout_path).write_text(proc.stdout or "")
    Path(stderr_path).write_text(proc.stderr or "")
    return proc.returncode


def policy_allows_execution(policy, approve_human):
    allowed_human = set(policy.get("allowedWithHumanApproval", []))
    allowed_auto = set(policy.get("allowedAutomaticActions", []))
    never_auto = set(policy.get("neverAutomatic", []))

    if ACTION in never_auto:
        return False, "BLOCKED_NEVER_AUTOMATIC"

    if ACTION in allowed_auto:
        return True, "AUTOMATIC_SAFE"

    if ACTION in allowed_human and approve_human:
        return True, "HUMAN_APPROVED"

    if ACTION in allowed_human and not approve_human:
        return False, "HUMAN_APPROVAL_REQUIRED"

    return False, "ACTION_NOT_ALLOWED_BY_POLICY"


def write_markdown(summary):
    lines = [
        "# Step 105 Policy-Gated On-Chain Audit-Anchor Validation",
        "",
        "## Purpose",
        "",
        "This report records policy-gated execution of Step 103 and Step 104 on-chain audit-anchor validation.",
        "",
        "## Result",
        "",
        f"- Run ID: `{summary['runId']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Overall status: **{summary['overallStatus']}**",
        f"- Policy decision: `{summary['policyDecision']}`",
        f"- Human approval supplied: `{summary['humanApprovalSupplied']}`",
        "",
        "## Executed / Planned Commands",
        "",
        "```bash",
        "npx hardhat run scripts/l4/submit_l4_audit_anchor_hardhat.js",
        "npx hardhat run scripts/l4/test_l4_audit_anchor_registry_negative_security.js",
        "```",
        "",
        "## Validation Summary",
        "",
        f"- Step 103 status: `{summary['step103Status']}`",
        f"- Step 104 status: `{summary['step104Status']}`",
        f"- Step 104 overall security result: `{summary.get('step104OverallStatus')}`",
        "",
        "## Research Meaning",
        "",
        "Step 105 integrates the on-chain audit-anchor registry validation into the policy-gated automation workflow.",
        "",
        "This means the project can now move from manual smart-contract validation to controlled, approval-gated, repeatable validation of blockchain audit anchoring.",
        "",
        "## Safety Boundary",
        "",
        "This runner uses local Hardhat execution only. It does not deploy to a public chain, use real funds, push code, submit papers, or modify Git history.",
        "",
        "## Generated Files",
        "",
        f"- Summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- Summary Markdown: `{rel(SUMMARY_MD)}`",
        f"- Step 103 stdout: `{rel(STEP103_STDOUT)}`",
        f"- Step 103 stderr: `{rel(STEP103_STDERR)}`",
        f"- Step 104 stdout: `{rel(STEP104_STDOUT)}`",
        f"- Step 104 stderr: `{rel(STEP104_STDERR)}`",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Execute local Hardhat on-chain validation.")
    parser.add_argument("--approve-human", action="store_true", help="Human approval gate for execution.")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    policy = read_json(POLICY_JSON, default={})

    allowed, policy_decision = policy_allows_execution(policy, args.approve_human)

    summary = {
        "experiment": "step105_policy_gated_onchain_anchor_validation",
        "runId": run_id,
        "mode": "execute" if args.execute else "dry-run",
        "action": ACTION,
        "policyDecision": policy_decision,
        "humanApprovalSupplied": bool(args.approve_human),
        "step103Command": f"npx hardhat run {STEP103_SCRIPT}",
        "step104Command": f"npx hardhat run {STEP104_SCRIPT}",
        "step103Status": "NOT_RUN",
        "step104Status": "NOT_RUN",
        "step104OverallStatus": None,
        "overallStatus": "DRY_RUN_READY",
        "summaryJson": rel(SUMMARY_JSON),
        "summaryMarkdown": rel(SUMMARY_MD),
    }

    if args.execute:
        if not allowed:
            summary["overallStatus"] = f"BLOCKED_{policy_decision}"
        else:
            step103_rc = run_cmd(["npx", "hardhat", "run", STEP103_SCRIPT], STEP103_STDOUT, STEP103_STDERR)
            step104_rc = run_cmd(["npx", "hardhat", "run", STEP104_SCRIPT], STEP104_STDOUT, STEP104_STDERR)

            summary["step103Status"] = "PASS" if step103_rc == 0 and STEP103_RESULT.exists() else "FAIL"
            summary["step104Status"] = "PASS" if step104_rc == 0 and STEP104_RESULT.exists() else "FAIL"

            step104_data = read_json(STEP104_RESULT, default={})
            summary["step104OverallStatus"] = step104_data.get("overallStatus")

            if summary["step103Status"] == "PASS" and summary["step104Status"] == "PASS" and summary["step104OverallStatus"] == "PASS":
                summary["overallStatus"] = "EXECUTED_PASS"
            else:
                summary["overallStatus"] = "EXECUTED_FAIL"

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    write_markdown(summary)

    print(json.dumps({
        "experiment": summary["experiment"],
        "runId": summary["runId"],
        "overallStatus": summary["overallStatus"],
        "policyDecision": summary["policyDecision"],
        "summaryJson": summary["summaryJson"],
        "summaryMarkdown": summary["summaryMarkdown"],
    }, indent=2))


if __name__ == "__main__":
    main()
