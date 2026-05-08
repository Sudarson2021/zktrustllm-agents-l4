#!/usr/bin/env python3

"""
Proper read-only MCP server for ZKTrustLLM Level 4.

This MCP server exposes blockchain-authenticated Level 4 context as MCP tools.

Role in Level 4:
- A2A carries compact references between agents.
- MCP lets receiving agents retrieve and verify authenticated context behind those references.
- Blockchain stores authenticated shared state.
- AUTH_V2.2 provides proof-governed admissibility.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from web3 import Web3


ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_FILE = ROOT / "deployments" / "l4.localhost.json"

DECISION_ATTESTOR_ARTIFACT = (
    ROOT
    / "artifacts"
    / "contracts"
    / "l4"
    / "DecisionAttestorAuthV2_2.sol"
    / "DecisionAttestorAuthV2_2.json"
)

A2A_REGISTRY_ARTIFACT = (
    ROOT
    / "artifacts"
    / "contracts"
    / "l4"
    / "A2AReferenceRegistry.sol"
    / "A2AReferenceRegistry.json"
)

MCP_RESULT_DIR = ROOT / "results" / "l4_mcp_server"

mcp = FastMCP("ZKTrustLLM-Level4-MCP")


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text())


def _connect():
    deployment = _load_json(DEPLOYMENT_FILE)

    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local Hardhat node at http://127.0.0.1:8545")

    attestor_address = deployment.get("decisionAttestorAuthV2_2")
    registry_address = deployment.get("a2aReferenceRegistry")

    if not attestor_address:
        raise RuntimeError("Missing decisionAttestorAuthV2_2 in deployments/l4.localhost.json")

    if not registry_address:
        raise RuntimeError("Missing a2aReferenceRegistry in deployments/l4.localhost.json")

    attestor_artifact = _load_json(DECISION_ATTESTOR_ARTIFACT)
    registry_artifact = _load_json(A2A_REGISTRY_ARTIFACT)

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(attestor_address),
        abi=attestor_artifact["abi"],
    )

    registry = w3.eth.contract(
        address=Web3.to_checksum_address(registry_address),
        abi=registry_artifact["abi"],
    )

    return w3, deployment, attestor, registry


def _hex32(value: Any) -> str:
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if hasattr(value, "hex"):
        raw = value.hex()
        return raw if raw.startswith("0x") else "0x" + raw
    return str(value)


@mcp.tool()
def get_auth_v2_2_decision(decision_id: int) -> Dict[str, Any]:
    """
    Retrieve an AUTH_V2.2 proof-backed decision from the blockchain.

    Args:
        decision_id: On-chain AUTH_V2.2 decision identifier.
    """
    start = time.perf_counter()
    _, deployment, attestor, _ = _connect()

    count = attestor.functions.decisionCount().call()
    if decision_id <= 0 or decision_id > count:
        return {
            "ok": False,
            "error": "decision_id out of range",
            "decisionCount": count,
            "decisionId": decision_id,
        }

    d = attestor.functions.getDecision(decision_id).call()
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "ok": True,
        "decisionAttestorAuthV2_2": deployment["decisionAttestorAuthV2_2"],
        "decisionId": decision_id,
        "decisionCount": count,
        "agentId": d[0],
        "capabilityId": _hex32(d[1]),
        "policyClassHash": _hex32(d[2]),
        "actionClass": int(d[3]),
        "contextHash": _hex32(d[4]),
        "traceCommitment": _hex32(d[5]),
        "expiryBucket": int(d[6]),
        "policyAdmissibilityFlag": int(d[7]),
        "trustState": int(d[8]),
        "timestamp": int(d[9]),
        "retrievalLatencyMs": latency_ms,
    }


@mcp.tool()
def get_a2a_reference(reference_id: int) -> Dict[str, Any]:
    """
    Retrieve a compact A2A reference record from the blockchain.

    Args:
        reference_id: On-chain A2A reference identifier.
    """
    start = time.perf_counter()
    _, deployment, _, registry = _connect()

    count = registry.functions.referenceCount().call()
    if reference_id <= 0 or reference_id > count:
        return {
            "ok": False,
            "error": "reference_id out of range",
            "referenceCount": count,
            "referenceId": reference_id,
        }

    r = registry.functions.getReference(reference_id).call()
    valid = registry.functions.isReferenceValid(reference_id).call()
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "ok": True,
        "a2aReferenceRegistry": deployment["a2aReferenceRegistry"],
        "referenceId": reference_id,
        "referenceCount": count,
        "valid": bool(valid),
        "exists": bool(r[0]),
        "senderAgentId": r[1],
        "receiverAgentId": r[2],
        "sourceDecisionId": int(r[3]),
        "sourceBlockNumber": int(r[4]),
        "capabilityId": _hex32(r[5]),
        "policyClassHash": _hex32(r[6]),
        "actionClass": int(r[7]),
        "contextHash": _hex32(r[8]),
        "traceCommitment": _hex32(r[9]),
        "cidHash": _hex32(r[10]),
        "proofRef": _hex32(r[11]),
        "expiryBucket": int(r[12]),
        "expiresAt": int(r[13]),
        "createdAt": int(r[14]),
        "retrievalLatencyMs": latency_ms,
    }


@mcp.tool()
def is_a2a_reference_valid(reference_id: int) -> Dict[str, Any]:
    """
    Check whether an A2A reference exists and is still valid.

    Args:
        reference_id: On-chain A2A reference identifier.
    """
    start = time.perf_counter()
    _, deployment, _, registry = _connect()

    count = registry.functions.referenceCount().call()
    valid = False
    if reference_id > 0 and reference_id <= count:
        valid = registry.functions.isReferenceValid(reference_id).call()

    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "ok": True,
        "a2aReferenceRegistry": deployment["a2aReferenceRegistry"],
        "referenceId": reference_id,
        "referenceCount": count,
        "valid": bool(valid),
        "retrievalLatencyMs": latency_ms,
    }


@mcp.tool()
def verify_reference_bundle(reference_id: int) -> Dict[str, Any]:
    """
    Verify that the A2A reference is internally consistent with its source AUTH_V2.2 decision.

    Args:
        reference_id: On-chain A2A reference identifier.
    """
    start = time.perf_counter()

    decision_result = None
    reference_result = get_a2a_reference(reference_id)

    if not reference_result.get("ok"):
        return {
            "ok": False,
            "referenceId": reference_id,
            "error": reference_result.get("error", "reference retrieval failed"),
            "reference": reference_result,
        }

    source_decision_id = int(reference_result["sourceDecisionId"])
    decision_result = get_auth_v2_2_decision(source_decision_id)

    if not decision_result.get("ok"):
        return {
            "ok": False,
            "referenceId": reference_id,
            "sourceDecisionId": source_decision_id,
            "error": decision_result.get("error", "decision retrieval failed"),
            "reference": reference_result,
            "decision": decision_result,
        }

    checks = {
        "senderAgentMatchesDecisionAgent": (
            reference_result["senderAgentId"] == decision_result["agentId"]
        ),
        "capabilityMatches": (
            reference_result["capabilityId"].lower() == decision_result["capabilityId"].lower()
        ),
        "policyClassMatches": (
            reference_result["policyClassHash"].lower() == decision_result["policyClassHash"].lower()
        ),
        "actionClassMatches": (
            int(reference_result["actionClass"]) == int(decision_result["actionClass"])
        ),
        "contextHashMatches": (
            reference_result["contextHash"].lower() == decision_result["contextHash"].lower()
        ),
        "traceCommitmentMatches": (
            reference_result["traceCommitment"].lower()
            == decision_result["traceCommitment"].lower()
        ),
        "expiryBucketMatches": (
            int(reference_result["expiryBucket"]) == int(decision_result["expiryBucket"])
        ),
        "referenceValid": bool(reference_result["valid"]),
        "policyAdmissible": int(decision_result["policyAdmissibilityFlag"]) == 1,
        "trustStateRestricted": int(decision_result["trustState"]) == 3,
        "actionClassIsolate": int(decision_result["actionClass"]) == 3,
    }

    bundle_valid = all(checks.values())
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    result = {
        "ok": True,
        "referenceId": reference_id,
        "sourceDecisionId": source_decision_id,
        "bundleValid": bundle_valid,
        "checks": checks,
        "reference": reference_result,
        "decision": decision_result,
        "bundleVerificationLatencyMs": latency_ms,
    }

    MCP_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = MCP_RESULT_DIR / "mcp_reference_bundle_verification.json"
    out_file.write_text(json.dumps(result, indent=2) + "\n")

    return result


@mcp.tool()
def get_level4_kpi_summary() -> Dict[str, Any]:
    """
    Return a summary of currently available Level 4 MCP/A2A KPIs.
    """
    start = time.perf_counter()

    bundle = verify_reference_bundle(1)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "ok": True,
        "level": "L4",
        "mcpRole": "structured context/tool access to blockchain-authenticated state",
        "a2aRole": "compact reference-based inter-agent coordination",
        "blockchainRole": "authenticated shared state",
        "zkRole": "proof-governed policy admissibility",
        "availableMeasuredKpis": {
            "referenceBundleValid": bundle.get("bundleValid"),
            "mcpBundleVerificationLatencyMs": bundle.get("bundleVerificationLatencyMs"),
            "mcpSummaryLatencyMs": latency_ms,
            "referenceId": bundle.get("referenceId"),
            "sourceDecisionId": bundle.get("sourceDecisionId"),
        },
        "futureNetworkKpis": [
            "control_response_time_ms",
            "control_plane_overhead_ratio",
            "jitter_during_control_event_ms",
            "packet_loss_during_orchestration_pct",
            "service_continuity_impact",
        ],
    }


if __name__ == "__main__":
    mcp.run()
