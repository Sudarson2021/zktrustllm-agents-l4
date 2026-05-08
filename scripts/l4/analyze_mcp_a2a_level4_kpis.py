#!/usr/bin/env python3

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

A2A_RESULT = ROOT / "results" / "l4_a2a_reference" / "a2a_reference_latest_decision.json"
MCP_RESULT = ROOT / "results" / "l4_mcp_server" / "mcp_tool_test_results.json"

OUT_DIR = ROOT / "results" / "l4_mcp_a2a_kpi"
OUT_JSON = OUT_DIR / "kpi_summary.json"
OUT_CSV = OUT_DIR / "kpi_summary.csv"
OUT_MD = OUT_DIR / "kpi_summary.md"


def compact_json_size(obj):
    return len(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def find_call(mcp_result, tool_name):
    for call in mcp_result.get("calls", []):
        if call.get("tool") == tool_name:
            return call
    return None


def main():
    if not A2A_RESULT.exists():
        raise FileNotFoundError(f"Missing A2A result: {A2A_RESULT}")

    if not MCP_RESULT.exists():
        raise FileNotFoundError(f"Missing MCP result: {MCP_RESULT}")

    a2a = json.loads(A2A_RESULT.read_text())
    mcp = json.loads(MCP_RESULT.read_text())

    decision_call = find_call(mcp, "get_auth_v2_2_decision")
    reference_call = find_call(mcp, "get_a2a_reference")
    valid_call = find_call(mcp, "is_a2a_reference_valid")
    bundle_call = find_call(mcp, "verify_reference_bundle")
    summary_call = find_call(mcp, "get_level4_kpi_summary")

    # Representative raw A2A payload:
    # This approximates the larger payload that would be sent if Agent A transmitted
    # raw context/evidence/policy information instead of a compact authenticated reference.
    raw_a2a_payload = {
        "senderAgentId": a2a["senderAgentId"],
        "receiverAgentId": a2a["receiverAgentId"],
        "task": "trust-aware-isolation-request",
        "networkContext": {
            "sliceId": "slice-5g-demo-01",
            "sessionType": "secure-multicast-video",
            "mediaPath": "DTLS/RTP/multicast",
            "latencyMs": 92,
            "jitterMs": 18,
            "packetLossPct": 2.4,
            "handoverState": "degraded",
            "controlNeed": "trust-aware-isolation"
        },
        "policyContext": {
            "policyClassHash": a2a["policyClassHash"],
            "actionClass": a2a["actionClass"],
            "trustState": "3",
            "admissibilityFlag": "1",
            "semanticRule": "Restricted trust state maps to isolate action"
        },
        "evidenceContext": {
            "contextHash": a2a["contextHash"],
            "traceCommitment": a2a["traceCommitment"],
            "cidHash": a2a["cidHash"],
            "proofRef": a2a["proofRef"],
            "expandedEvidenceSummary": (
                "Representative expanded raw evidence/policy context that would "
                "otherwise be exchanged directly between agents in an L4-raw mode."
            )
        },
        "auditContext": {
            "sourceDecisionId": a2a["sourceDecisionId"],
            "referenceId": a2a["referenceId"],
            "txHash": a2a["txHash"],
            "sourceBlockNumber": a2a["sourceBlockNumber"]
        }
    }

    # Compact reference-based A2A payload:
    reference_a2a_payload = {
        "senderAgentId": a2a["senderAgentId"],
        "receiverAgentId": a2a["receiverAgentId"],
        "referenceId": a2a["referenceId"],
        "sourceDecisionId": a2a["sourceDecisionId"],
        "sourceBlockNumber": a2a["sourceBlockNumber"],
        "capabilityId": a2a["capabilityId"],
        "policyClassHash": a2a["policyClassHash"],
        "actionClass": a2a["actionClass"],
        "contextHash": a2a["contextHash"],
        "traceCommitment": a2a["traceCommitment"],
        "cidHash": a2a["cidHash"],
        "proofRef": a2a["proofRef"],
        "expiryBucket": a2a["expiryBucket"]
    }

    raw_bytes = compact_json_size(raw_a2a_payload)
    ref_bytes = compact_json_size(reference_a2a_payload)
    compression_gain = 1.0 - (ref_bytes / raw_bytes)

    bundle_result = bundle_call["result"] if bundle_call else {}
    decision_result = decision_call["result"] if decision_call else {}
    reference_result = reference_call["result"] if reference_call else {}

    kpis = {
        "experiment": "level4_mcp_a2a_kpi_analysis",
        "network": a2a["network"],

        "a2a": {
            "sourceDecisionId": a2a["sourceDecisionId"],
            "referenceId": a2a["referenceId"],
            "referenceValid": bool(a2a["valid"]),
            "referenceRegistrationGas": int(a2a["gasUsed"]),
            "senderAgentId": a2a["senderAgentId"],
            "receiverAgentId": a2a["receiverAgentId"],
            "actionClass": a2a["actionClass"],
            "referenceReuseRatioSingleRun": 1.0,
        },

        "mcp": {
            "listedToolCount": len(mcp.get("listedTools", [])),
            "toolCallCount": int(mcp.get("toolCallCount", 0)),
            "successfulToolCalls": int(mcp.get("successfulToolCalls", 0)),
            "mcpContextRetrievalSuccessRate": float(mcp.get("mcpContextRetrievalSuccessRate", 0)),
            "averageToolInvocationLatencyMs": float(mcp.get("averageToolInvocationLatencyMs", 0)),
            "maxToolInvocationLatencyMs": float(mcp.get("maxToolInvocationLatencyMs", 0)),
            "decisionRetrievalLatencyMs": decision_result.get("retrievalLatencyMs"),
            "referenceRetrievalLatencyMs": reference_result.get("retrievalLatencyMs"),
            "referenceValidityCheckLatencyMs": valid_call["result"].get("retrievalLatencyMs") if valid_call else None,
            "bundleVerificationLatencyMs": bundle_result.get("bundleVerificationLatencyMs"),
            "bundleValid": bool(bundle_result.get("bundleValid", False)),
        },

        "proof_policy": {
            "policyAdmissibilityFlag": decision_result.get("policyAdmissibilityFlag"),
            "trustState": decision_result.get("trustState"),
            "actionClass": decision_result.get("actionClass"),
            "policyAdmissibilityObserved": decision_result.get("policyAdmissibilityFlag") == 1,
            "trustAwareActionObserved": (
                decision_result.get("trustState") == 3
                and decision_result.get("actionClass") == 3
            ),
        },

        "message_size": {
            "rawA2AMessageBytes": raw_bytes,
            "referenceA2AMessageBytes": ref_bytes,
            "coordinationCompressionGain": round(compression_gain, 4),
            "coordinationCompressionGainPercent": round(compression_gain * 100, 2),
        },

        "network_kpis": {
            "controlMessageSizeRawBytes": raw_bytes,
            "controlMessageSizeReferenceBytes": ref_bytes,
            "controlPlaneOverheadRatioReferenceVsRaw": round(ref_bytes / raw_bytes, 4),
            "controlResponseTimeMs": "not yet measured - requires event-to-action timestamps",
            "jitterDuringControlEventMs": "not yet measured - requires media/control telemetry",
            "packetLossDuringOrchestrationPct": "not yet measured - requires DTLS/RTP/VLC telemetry",
            "containmentTimeMs": "not yet measured - requires isolation/rekey completion timestamps",
            "serviceContinuityImpact": "not yet measured - requires media playback metrics",
            "recoveryTimeMs": "not yet measured - requires post-action stability timestamp",
        }
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(kpis, indent=2) + "\n")

    rows = [
        ("MCP tools listed", kpis["mcp"]["listedToolCount"], "measured"),
        ("MCP successful tool calls", kpis["mcp"]["successfulToolCalls"], "measured"),
        ("MCP context retrieval success rate", kpis["mcp"]["mcpContextRetrievalSuccessRate"], "measured"),
        ("MCP average tool invocation latency ms", kpis["mcp"]["averageToolInvocationLatencyMs"], "measured"),
        ("MCP max tool invocation latency ms", kpis["mcp"]["maxToolInvocationLatencyMs"], "measured"),
        ("MCP bundle verification latency ms", kpis["mcp"]["bundleVerificationLatencyMs"], "measured"),
        ("MCP bundle valid", kpis["mcp"]["bundleValid"], "measured"),
        ("A2A reference valid", kpis["a2a"]["referenceValid"], "measured"),
        ("A2A reference registration gas", kpis["a2a"]["referenceRegistrationGas"], "measured"),
        ("Reference reuse ratio single run", kpis["a2a"]["referenceReuseRatioSingleRun"], "single-run measured path"),
        ("Raw A2A message bytes", raw_bytes, "derived representative raw payload"),
        ("Reference A2A message bytes", ref_bytes, "derived compact reference payload"),
        ("Coordination compression gain percent", kpis["message_size"]["coordinationCompressionGainPercent"], "derived"),
        ("Policy admissibility observed", kpis["proof_policy"]["policyAdmissibilityObserved"], "measured"),
        ("Trust-aware action observed", kpis["proof_policy"]["trustAwareActionObserved"], "measured")
    ]

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["kpi", "value", "status"])
        writer.writerows(rows)

    md_lines = [
        "# Level 4 MCP/A2A KPI Summary",
        "",
        "## Measured Agent KPIs",
        "",
        f"- MCP tools listed: {kpis['mcp']['listedToolCount']}",
        f"- MCP successful tool calls: {kpis['mcp']['successfulToolCalls']}/{kpis['mcp']['toolCallCount']}",
        f"- MCP context retrieval success rate: {kpis['mcp']['mcpContextRetrievalSuccessRate']}",
        f"- MCP average tool invocation latency: {kpis['mcp']['averageToolInvocationLatencyMs']} ms",
        f"- MCP maximum tool invocation latency: {kpis['mcp']['maxToolInvocationLatencyMs']} ms",
        f"- MCP bundle verification latency: {kpis['mcp']['bundleVerificationLatencyMs']} ms",
        f"- MCP reference bundle valid: {kpis['mcp']['bundleValid']}",
        "",
        "## Measured A2A / Proof KPIs",
        "",
        f"- AUTH_V2.2 source decision ID: {kpis['a2a']['sourceDecisionId']}",
        f"- A2A reference ID: {kpis['a2a']['referenceId']}",
        f"- A2A reference valid: {kpis['a2a']['referenceValid']}",
        f"- A2A reference registration gas: {kpis['a2a']['referenceRegistrationGas']}",
        f"- Policy admissibility observed: {kpis['proof_policy']['policyAdmissibilityObserved']}",
        f"- Trust-aware action observed: {kpis['proof_policy']['trustAwareActionObserved']}",
        "",
        "## Derived Message-Size KPIs",
        "",
        f"- Raw A2A message bytes: {raw_bytes}",
        f"- Reference A2A message bytes: {ref_bytes}",
        f"- Coordination compression gain: {kpis['message_size']['coordinationCompressionGainPercent']}%",
        "",
        "## Network KPI Status",
        "",
        "- Current network-facing KPI output covers control-message size and reference-vs-raw control overhead.",
        "- Jitter, packet loss, containment time, service continuity, and recovery time require the next telemetry wrapper over DTLS/RTP/VLC or emulated network traces.",
        "",
        "## Interpretation",
        "",
        "The current Level 4 result shows that A2A can exchange a compact authenticated reference, while MCP can retrieve and verify the authenticated blockchain context behind that reference. This supports the claim that blockchain acts as authenticated shared memory, MCP provides structured context/tool access, and A2A provides compact inter-agent coordination."
    ]

    OUT_MD.write_text("\n".join(md_lines) + "\n")

    print(json.dumps(kpis, indent=2))
    print(f"Saved JSON: {OUT_JSON}")
    print(f"Saved CSV : {OUT_CSV}")
    print(f"Saved MD  : {OUT_MD}")


if __name__ == "__main__":
    main()
