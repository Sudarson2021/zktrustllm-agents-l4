import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestor.sol" / "DecisionAttestor.json"
AR_ART = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"
CM_ART = ROOT / "artifacts" / "contracts" / "l4" / "CapabilityManager.sol" / "CapabilityManager.json"

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
        "gas": tx.get("gas", 900000),
        "maxFeePerGas": tx.get("maxFeePerGas", w3.to_wei(2, "gwei")),
        "maxPriorityFeePerGas": tx.get("maxPriorityFeePerGas", w3.to_wei(1, "gwei")),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def recover_agent_from_chain(w3, dep):
    ar_art = load_json(AR_ART)
    cm_art = load_json(CM_ART)

    ar = w3.eth.contract(
        address=Web3.to_checksum_address(dep["agentRegistry"]),
        abi=ar_art["abi"]
    )
    cm = w3.eth.contract(
        address=Web3.to_checksum_address(dep["capabilityManager"]),
        abi=cm_art["abi"]
    )

    if not ar.functions.isRegistered(TARGET_AGENT).call():
        raise RuntimeError(f"{TARGET_AGENT} is not registered on-chain")

    target_agent_key = ar.functions.agentKey(TARGET_AGENT).call().hex().lower()

    events = cm.events.CapabilityIssued().get_logs(from_block=0, to_block='latest')
    latest = None

    for ev in events:
        capability_id = ev["args"]["capabilityId"].hex().lower()
        agent_key = ev["args"]["agentKey"].hex().lower()
        policy_class = ev["args"]["policyClass"]
        block_number = int(ev["blockNumber"])

        if agent_key == target_agent_key:
            if latest is None or block_number >= latest["blockNumber"]:
                latest = {
                    "capabilityId": capability_id,
                    "agentKey": agent_key,
                    "policyClass": policy_class,
                    "blockNumber": block_number,
                }

    if latest is None:
        raise RuntimeError(f"No capability found on-chain for {TARGET_AGENT}")

    return {
        "agentId": TARGET_AGENT,
        "capabilityId": latest["capabilityId"],
        "policyClass": latest["policyClass"],
    }

def load_or_recover_agent(w3, dep):
    if REG_FILE.exists():
        reg = load_json(REG_FILE)
        for a in reg["agents"]:
            if a["agentId"] == TARGET_AGENT:
                return a

    print("[INFO] registered_agents.localhost.json missing or incomplete; recovering from chain")
    return recover_agent_from_chain(w3, dep)

def main():
    dep = load_json(DEPLOY_FILE)
    att_art = load_json(ATT_ART)
    trace = load_json(TRACE_FILE)
    cid = load_json(CID_FILE)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(dep["decisionAttestor"]),
        abi=att_art["abi"]
    )

    edge = load_or_recover_agent(w3, dep)

    tx = attestor.functions.submitAgentDecisionMock(
        edge["agentId"],
        Web3.to_bytes(hexstr="0x" + edge["capabilityId"].replace("0x", "")),
        Web3.to_bytes(hexstr=trace["contextHash"]),
        Web3.to_bytes(hexstr=trace["traceCommitment"]),
        cid["cid"],
        edge["policyClass"],
        trace["policyAction"]
    ).build_transaction({"from": account.address, "gas": 900000})

    receipt = send_tx(w3, account, tx)

    decision_count = attestor.functions.decisionCount().call()
    record = attestor.functions.decisions(decision_count).call()

    print("Submitted mock decision tx ->", receipt["transactionHash"].hex())
    print("Decision count ->", decision_count)
    print("Stored decision agentId ->", record[0])
    print("Stored policyClass ->", record[5])
    print("Stored action ->", record[6])
    print("Stored traceCID ->", record[4])

if __name__ == "__main__":
    main()
