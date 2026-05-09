# Step 97 Closed-Loop KPI Decision Agent

## Purpose

Step 97 introduces a closed-loop KPI decision agent for the Level 4 ZKTrustLLM-Agents workflow.

The purpose is to move beyond manual experiment execution and toward minimally supervised scientific automation.

## What the Agent Does

The agent reads current Level 4 KPI outputs from:

- MCP tool validation,
- semi-live MCP/A2A control-plane telemetry,
- multi-agent scaling telemetry,
- live RTP media-plane telemetry,
- DTLS-wrapped RTP media-plane validation,
- loopback network impairment matrix,
- Linux namespace impairment matrix,
- Step 96 agentic automation summary.

It validates the artifacts using threshold-based KPI checks and recommends the next safe workflow action.

## Decision Actions

Possible actions include:

- `RERUN_MCP_TOOL_VALIDATION`
- `RERUN_CONTROL_TELEMETRY`
- `RERUN_MULTI_AGENT_SCALING`
- `RERUN_CLEAN_RTP_BASELINE`
- `RERUN_DTLS_RTP_VALIDATION`
- `RERUN_LOOPBACK_IMPAIRMENT_MATRIX`
- `RERUN_NAMESPACE_IMPAIRMENT_MATRIX`
- `RERUN_FULL_AGENTIC_AUTOMATION`
- `GENERATE_SUPERVISOR_REPORT`
- `REVIEW_REQUIRED`

## Human-in-the-Loop Boundary

The decision agent does not automatically push code, deploy systems, run privileged commands, submit papers, or make irreversible research decisions.

It produces a recommendation that must be reviewed by the researcher or supervisor.

## Main Artifacts

- Script:
  - `scripts/l4/run_closed_loop_kpi_decision_agent.py`

- Decision JSON:
  - `results/l4_closed_loop_agent/closed_loop_kpi_decision.json`

- Decision Markdown:
  - `results/l4_closed_loop_agent/closed_loop_kpi_decision.md`

- Decision CSV:
  - `results/l4_closed_loop_agent/closed_loop_kpi_checks.csv`

## Research Meaning

This step introduces the first closed-loop decision layer in the L4 workflow.

Step 96 automated experiment execution. Step 97 adds reasoning over generated KPIs and recommends the next action.

This creates the foundation for the next stage: a controlled remediation executor that can run the recommended action in dry-run mode first and only execute after human approval.
