#!/usr/bin/env python3

import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "out_l4"

FIELD_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617

def fhash(text: str) -> int:
    return int.from_bytes(Web3.keccak(text=text), byteorder="big") % FIELD_MODULUS

def hx(value: int) -> str:
    return "0x" + int(value).to_bytes(32, byteorder="big").hex()

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    agent_id = "policy-lkh-01"
    receiver_agent_id = "policy-lkh-agent-01"

    binding_nonce = 20260508

    agent_key = fhash(f"agent:{agent_id}")
    capability_id = fhash("capability:lkh:isolate")
    policy_class_hash = fhash("policy:restricted-isolate")
    action_class = 3
    context_hash = fhash("context:mcp-a2a-l4-reference-bound")
    expiry_bucket = 493129
    policy_admissibility_flag = 1
    trust_state = 3

    reference_context_hash = fhash(
        "referenceContext:"
        "sourceDecisionId=1:"
        "referenceId=1:"
        "mcpTool=verify_reference_bundle:"
        "a2aMode=compact-reference"
    )

    coordination_session_id = fhash(
        "coordinationSession:l4-step81-auth-v2-3-reference-bound-proof"
    )

    trace_commitment = (
        reference_context_hash + coordination_session_id + binding_nonce
    ) % FIELD_MODULUS

    public_inputs_order = [
        "agentKey",
        "capabilityId",
        "policyClassHash",
        "actionClass",
        "contextHash",
        "traceCommitment",
        "expiryBucket",
        "policyAdmissibilityFlag",
        "trustState",
        "referenceContextHash",
        "coordinationSessionId",
    ]

    public_inputs = {
        "agentKey": agent_key,
        "capabilityId": capability_id,
        "policyClassHash": policy_class_hash,
        "actionClass": action_class,
        "contextHash": context_hash,
        "traceCommitment": trace_commitment,
        "expiryBucket": expiry_bucket,
        "policyAdmissibilityFlag": policy_admissibility_flag,
        "trustState": trust_state,
        "referenceContextHash": reference_context_hash,
        "coordinationSessionId": coordination_session_id,
    }

    payload = {
        "relationVersion": "auth_v2_3_reference_bound_relation",
        "agentId": agent_id,
        "receiverAgentId": receiver_agent_id,
        "description": "AUTH_V2.3 proof binds policy-admissible decision to MCP/A2A reference context.",
        "privateInputs": {
            "bindingNonce": binding_nonce
        },
        "publicInputsOrder": public_inputs_order,
        "publicInputs": {k: str(v) for k, v in public_inputs.items()},
        "publicInputsHex": {k: hx(v) for k, v in public_inputs.items()},
        "referenceBinding": {
            "sourceDecisionId": "1",
            "referenceId": "1",
            "referenceContextHash": str(reference_context_hash),
            "referenceContextHashHex": hx(reference_context_hash),
            "coordinationSessionId": str(coordination_session_id),
            "coordinationSessionIdHex": hx(coordination_session_id),
            "traceCommitment": str(trace_commitment),
            "traceCommitmentHex": hx(trace_commitment),
            "bindingFormula": "traceCommitment = referenceContextHash + coordinationSessionId + bindingNonce"
        }
    }

    proof_payload_file = OUT / "proof_payload.auth_v2_3.json"
    circuit_input_file = OUT / "circuit_input.auth_v2_3.json"
    zokrates_input_file = OUT / "zokrates_input.auth_v2_3.json"
    flat_args_file = OUT / "auth_v2_3.flat_args.txt"

    proof_payload_file.write_text(json.dumps(payload, indent=2) + "\n")

    circuit_input = {
        "privateInputs": payload["privateInputs"],
        "publicInputsOrder": public_inputs_order,
        "publicInputs": payload["publicInputs"],
        "publicInputsHex": payload["publicInputsHex"]
    }
    circuit_input_file.write_text(json.dumps(circuit_input, indent=2) + "\n")

    flat_args = [str(binding_nonce)] + [str(public_inputs[k]) for k in public_inputs_order]

    zokrates_input = {
        "argumentOrder": ["bindingNonce"] + public_inputs_order,
        "arguments": flat_args,
        "privateArgumentOrder": ["bindingNonce"],
        "publicArgumentOrder": public_inputs_order
    }
    zokrates_input_file.write_text(json.dumps(zokrates_input, indent=2) + "\n")
    flat_args_file.write_text(" ".join(flat_args) + "\n")

    print(f"Saved AUTH_V2.3 proof payload -> {proof_payload_file}")
    print(f"Saved AUTH_V2.3 circuit input  -> {circuit_input_file}")
    print(f"Saved AUTH_V2.3 ZoKrates input -> {zokrates_input_file}")
    print(f"Saved AUTH_V2.3 flat args      -> {flat_args_file}")
    print("relationVersion -> auth_v2_3_reference_bound_relation")
    print("agentId ->", agent_id)
    print("receiverAgentId ->", receiver_agent_id)
    print("trustState ->", trust_state)
    print("actionClass ->", action_class)
    print("policyAdmissibilityFlag ->", policy_admissibility_flag)
    print("referenceContextHash ->", hx(reference_context_hash))
    print("coordinationSessionId ->", hx(coordination_session_id))
    print("traceCommitment ->", hx(trace_commitment))

if __name__ == "__main__":
    main()
