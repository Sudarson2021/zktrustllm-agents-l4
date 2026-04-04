import json
import os
import subprocess
import time
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")

REG_FILE = ROOT / "artifacts" / "out_l4" / "registered_agents.localhost.json"
TRACE_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.json"
CID_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.cid.json"

OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "auth_v1_inputs.task-0001.json"

CONFIG_DIR = ROOT / "configs" / "l4"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
TEST_VECTOR_FILE = CONFIG_DIR / "test_vectors_auth_v1.json"

TARGET_AGENT = "edge-telemetry-01"

ACTION_CODES = {
    "keep": 1,
    "rekey": 2,
    "rotate": 3,
    "isolate": 4,
    "quarantine": 5,
}

SCOPE_TEXTS = {
    "edge-telemetry-01": "tenant-3:collect-context",
    "trust-risk-01": "tenant-3:evaluate-risk",
    "policy-lkh-01": "tenant-3:bounded-lkh-action",
}

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def ensure_local_artifacts():
    subprocess.run(["python3", "scripts/l4/refresh_capabilities.py"], check=True)
    subprocess.run(["python3", "scripts/l4/export_registered_agents.py"], check=True)

    if not TRACE_FILE.exists():
        subprocess.run(["python3", "scripts/l4/create_trace_bundle.py"], check=True)

    if not CID_FILE.exists():
        subprocess.run(["python3", "scripts/l4/pin_trace_bundle.py"], check=True)

def h(txt: str) -> str:
    return Web3.keccak(text=txt).hex()

def norm32(hex_str: str) -> str:
    x = hex_str.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    if len(x) != 66:
        raise ValueError(f"Expected 32-byte hex string, got: {x}")
    return x

def main():
    ensure_local_artifacts()

    reg = load_json(REG_FILE)
    trace = load_json(TRACE_FILE)
    cid = load_json(CID_FILE)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    edge = None
    for a in reg["agents"]:
        if a["agentId"] == TARGET_AGENT:
            edge = a
            break

    if edge is None:
        raise RuntimeError(f"{TARGET_AGENT} not found in registered agents")

    action = trace["policyAction"]
    if action not in ACTION_CODES:
        raise RuntimeError(f"Unsupported action for auth_v1: {action}")

    expiry_bucket = int(os.getenv("AUTH_V1_EXPIRY_BUCKET", str(int(time.time() // 3600))))
    capability_salt = os.getenv("AUTH_V1_CAPABILITY_SALT", "0x" + "00" * 32)

    agent_key = norm32(edge["agentKey"])
    capability_id = norm32(edge["capabilityId"])
    policy_class_hash = h(edge["policyClass"])
    context_hash = norm32(trace["contextHash"])
    trace_commitment = norm32(trace["traceCommitment"])
    action_hash = h(action)

    scope_text = SCOPE_TEXTS[TARGET_AGENT]
    scope_hash = h(scope_text)

    domain_sep_capability = h("ZKTrustLLM-Agents/auth_v1/capability")
    domain_sep_action = h("ZKTrustLLM-Agents/auth_v1/action")

    action_code = ACTION_CODES[action]

    # Draft witness-side commitments for the future auth_v1 circuit.
    # These are NOT yet required to equal the current on-chain capabilityId.
    capability_witness_digest = w3.keccak(
        w3.codec.encode(
            ["bytes32", "bytes32", "bytes32", "bytes32", "uint256", "bytes32"],
            [
                Web3.to_bytes(hexstr=domain_sep_capability),
                Web3.to_bytes(hexstr=agent_key),
                Web3.to_bytes(hexstr=policy_class_hash),
                Web3.to_bytes(hexstr=scope_hash),
                expiry_bucket,
                Web3.to_bytes(hexstr=norm32(capability_salt)),
            ],
        )
    ).hex()

    action_witness_digest = w3.keccak(
        w3.codec.encode(
            ["bytes32", "uint256"],
            [
                Web3.to_bytes(hexstr=domain_sep_action),
                action_code,
            ],
        )
    ).hex()

    public_input_digest = w3.keccak(
        w3.codec.encode(
            ["bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "uint256"],
            [
                Web3.to_bytes(hexstr=agent_key),
                Web3.to_bytes(hexstr=capability_id),
                Web3.to_bytes(hexstr=policy_class_hash),
                Web3.to_bytes(hexstr=context_hash),
                Web3.to_bytes(hexstr=trace_commitment),
                Web3.to_bytes(hexstr=action_hash),
                expiry_bucket,
            ],
        )
    ).hex()

    out = {
        "meta": {
            "taskId": trace["taskId"],
            "targetAgent": TARGET_AGENT,
            "generatedAt": int(time.time()),
            "traceCID": cid["cid"],
            "note": "auth_v1 deterministic input set for future real authorization proof",
        },
        "publicInputs": {
            "agentKey": agent_key,
            "capabilityId": capability_id,
            "policyClassHash": policy_class_hash,
            "contextHash": context_hash,
            "traceCommitment": trace_commitment,
            "actionHash": action_hash,
            "expiryBucket": expiry_bucket,
        },
        "witnessPlaceholders": {
            "scopeText": scope_text,
            "scopeHash": scope_hash,
            "capabilitySalt": norm32(capability_salt),
            "actionCode": action_code,
            "domainSepCapability": domain_sep_capability,
            "domainSepAction": domain_sep_action,
        },
        "derivedDigests": {
            "capabilityWitnessDigestDraft": capability_witness_digest,
            "actionWitnessDigestDraft": action_witness_digest,
            "publicInputDigest": public_input_digest,
        },
        "currentRuntimeValues": {
            "agentId": edge["agentId"],
            "policyClass": edge["policyClass"],
            "action": action,
            "traceCID": cid["cid"],
        },
    }

    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    with open(TEST_VECTOR_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved auth_v1 inputs ->", OUT_FILE)
    print("Saved auth_v1 test vector ->", TEST_VECTOR_FILE)
    print("Public input digest ->", public_input_digest)

if __name__ == "__main__":
    main()
