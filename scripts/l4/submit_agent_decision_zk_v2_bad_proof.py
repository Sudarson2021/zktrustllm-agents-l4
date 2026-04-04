import json
import os
import subprocess
import time
from pathlib import Path
from web3 import Web3
from web3.exceptions import ContractLogicError

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorZK.sol" / "DecisionAttestorZK.json"
REG_FILE = ROOT / "artifacts" / "out_l4" / "registered_agents.localhost.json"
TRACE_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.json"
CID_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.cid.json"
AR_ART = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"

TARGET_AGENT = "edge-telemetry-01"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def ensure_local_artifacts():
    subprocess.run(["python3", "scripts/l4/refresh_capabilities.py"], check=True)
    subprocess.run(["python3", "scripts/l4/export_registered_agents.py"], check=True)

    if not TRACE_FILE.exists():
        subprocess.run(["python3", "scripts/l4/create_trace_bundle.py"], check=True)

    if not CID_FILE.exists():
        subprocess.run(["python3", "scripts/l4/pin_trace_bundle.py"], check=True)

def main():
    ensure_local_artifacts()

    dep = load_json(DEPLOY_FILE)
    att_art = load_json(ATT_ART)
    reg = load_json(REG_FILE)
    trace = load_json(TRACE_FILE)
    cid = load_json(CID_FILE)
    ar_art = load_json(AR_ART)

    if "decisionAttestorZKV2" not in dep:
        raise RuntimeError("decisionAttestorZKV2 not found in deployments/l4.localhost.json")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(dep["decisionAttestorZKV2"]),
        abi=att_art["abi"]
    )

    agent_registry = w3.eth.contract(
        address=Web3.to_checksum_address(dep["agentRegistry"]),
        abi=ar_art["abi"]
    )

    edge = None
    for a in reg["agents"]:
        if a["agentId"] == TARGET_AGENT:
            edge = a
            break

    if edge is None:
        raise RuntimeError(f"{TARGET_AGENT} not found")

    capability_id_bytes = Web3.to_bytes(hexstr="0x" + edge["capabilityId"].replace("0x", ""))
    context_hash_bytes = Web3.to_bytes(hexstr=trace["contextHash"])
    trace_commitment_bytes = Web3.to_bytes(hexstr=trace["traceCommitment"])
    policy_class_hash = w3.keccak(text=edge["policyClass"])
    correct_action_hash = w3.keccak(text=trace["policyAction"])
    wrong_action_hash = w3.keccak(text="quarantine")
    expiry_bucket = int(time.time() // 3600)
    agent_key = agent_registry.functions.agentKey(edge["agentId"]).call()

    # Deliberately malformed proof blob: wrong action hash
    bad_proof_blob = w3.codec.encode(
        ["bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "uint256"],
        [
            agent_key,
            capability_id_bytes,
            policy_class_hash,
            context_hash_bytes,
            trace_commitment_bytes,
            wrong_action_hash,
            expiry_bucket
        ]
    )

    try:
        attestor.functions.submitAgentDecisionZK(
            edge["agentId"],
            capability_id_bytes,
            context_hash_bytes,
            trace_commitment_bytes,
            cid["cid"],
            edge["policyClass"],
            trace["policyAction"],   # correct action string
            expiry_bucket,
            bad_proof_blob           # wrong action hash encoded inside proof blob
        ).call({"from": account.address})

        raise SystemExit("ERROR: bad proof was unexpectedly accepted")

    except Exception as e:
        msg = str(e)
        print("Expected rejection captured")
        print(msg)

        if "authorization proof failed" not in msg:
            raise SystemExit(f"Unexpected error reason: {msg}")

if __name__ == "__main__":
    main()
