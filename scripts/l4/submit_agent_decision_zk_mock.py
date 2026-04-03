import json
import os
import subprocess
import time
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorZK.sol" / "DecisionAttestorZK.json"
REG_FILE = ROOT / "artifacts" / "out_l4" / "registered_agents.localhost.json"
TRACE_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.json"
CID_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "trace_bundle.task-0001.cid.json"

TARGET_AGENT = "edge-telemetry-01"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def send_tx(w3, account, tx):
    nonce = w3.eth.get_transaction_count(account.address)
    tx.update({
        "from": account.address,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
        "gas": tx.get("gas", 1200000),
        "maxFeePerGas": tx.get("maxFeePerGas", w3.to_wei(2, "gwei")),
        "maxPriorityFeePerGas": tx.get("maxPriorityFeePerGas", w3.to_wei(1, "gwei")),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

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

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(dep["decisionAttestorZK"]),
        abi=att_art["abi"]
    )

    edge = None
    for a in reg["agents"]:
        if a["agentId"] == TARGET_AGENT:
            edge = a
            break

    if edge is None:
        raise RuntimeError(f"{TARGET_AGENT} not found")

    expiry_bucket = int(time.time() // 3600)
    proof_blob = Web3.to_bytes(hexstr="0x1234")

    tx = attestor.functions.submitAgentDecisionZK(
        edge["agentId"],
        Web3.to_bytes(hexstr="0x" + edge["capabilityId"].replace("0x", "")),
        Web3.to_bytes(hexstr=trace["contextHash"]),
        Web3.to_bytes(hexstr=trace["traceCommitment"]),
        cid["cid"],
        edge["policyClass"],
        trace["policyAction"],
        expiry_bucket,
        proof_blob
    ).build_transaction({"from": account.address, "gas": 1200000})

    receipt = send_tx(w3, account, tx)

    count = attestor.functions.zkDecisionCount().call()
    record = attestor.functions.zkDecisions(count).call()

    print("Submitted ZK mock decision tx ->", receipt["transactionHash"].hex())
    print("ZK decision count ->", count)
    print("Stored decision agentId ->", record[0])
    print("Stored policyClass ->", record[5])
    print("Stored action ->", record[6])
    print("Stored traceCID ->", record[4])
    print("Stored expiryBucket ->", record[7])

if __name__ == "__main__":
    main()
