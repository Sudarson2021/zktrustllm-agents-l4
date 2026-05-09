# Step 96 L4 Agentic Automation Suite

## Purpose

Step 96 introduces the first full agentic automation suite for the ZKTrustLLM-Agents Level 4 workflow.

The goal is to reduce manual experiment execution and move the project toward reproducible, minimally supervised scientific automation while keeping supervisor review and human approval for sensitive actions.

## Automated Workflow

The suite currently orchestrates:

1. MCP Level 4 tool validation.
2. Semi-live MCP/A2A control-plane telemetry.
3. Multi-agent MCP/A2A scaling telemetry.
4. Live RTP media-plane telemetry.
5. DTLS-wrapped RTP media-plane validation.
6. DTLS/RTP arrival-gap jitter recomputation.
7. Optional loopback network impairment evaluation using Linux tc netem.
8. Optional Linux namespace impairment evaluation using veth and tc netem.

## Execution Commands

Standard non-privileged run:

    python scripts/l4/run_l4_agentic_automation_suite.py

Full privileged run:

    sudo -v
    python scripts/l4/run_l4_agentic_automation_suite.py --include-privileged

## Latest Full PASS Run

The latest privileged run completed successfully.

| Item | Value |
|---|---|
| Run ID | 20260509_164507 |
| Overall status | PASS |
| Output directory | results/l4_agentic_automation/run_20260509_164507 |
| Summary JSON | results/l4_agentic_automation/agentic_automation_summary.json |
| Summary Markdown | results/l4_agentic_automation/agentic_automation_summary.md |
| Artifact manifest | results/l4_agentic_automation/agentic_automation_artifact_manifest.csv |

## Scientific Meaning

Step 96 converts the Level 4 workflow from manual experimental execution into a repeatable automation pipeline.

It links proof-governed MCP/A2A control-plane validation, multi-agent scaling, RTP media-plane telemetry, DTLS-wrapped RTP validation, loopback impairment, namespace impairment, artifact manifest generation, and supervisor-readable progress reporting.

## Human-in-the-Loop Boundary

This automation suite does not automatically push code, submit papers, deploy public systems, or make irreversible research decisions. These actions remain human-approved.

## Why This Matters for the PhD Milestone

This step moves the project from isolated experiments toward a reproducible agentic research workflow.

The project can now automatically execute, validate, and document the major L4 control-plane and media-plane experiments. This provides a strong foundation for the next milestone: closed-loop KPI-based agentic decision-making.

## Next Step

Step 97 should implement a closed-loop KPI decision agent that reads current experiment summaries, compares them against thresholds, and automatically decides whether to run baseline RTP, DTLS-RTP, impairment, namespace, or report-generation workflows.
