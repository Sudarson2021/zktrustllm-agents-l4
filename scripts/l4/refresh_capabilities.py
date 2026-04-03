import json
import os
import time
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
NETWORK = os.getenv("L4_NETWORK", "localhost")
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")

DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

TTL_SECONDS = int(os.getenv("L4_CAP_TTL", "86400"))  # default: 24h for demo reliability

DEPLOY_FILE = ROOT / "deployments" / f"l4.{NETWORK}.json"
AR_ART = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"
CM_ART = ROOT / "artifacts" / "contracts" / "l4" / "CapabilityManager.sol" / "CapabilityManager.json"

OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / f"refreshed_capabilities.{NETWORK}.json"

AGENTS = [
    {
        "agentId": "edge-telemetry-01",
        "policyClass": "context-collect",
        "scopeText": "tenant-3:collect-context"
    },
    {
        "agentId": "trust-risk-01",
        "policyClass": "risk-eval",
        "scopeText": "tenant-3:evaluate-risk"
    },
    {
        "agentId": "policy-lkh-01",
        "policyClass": "lkh-control",
        "scopeText": "tenant-3:bounded-lkh-action"
    }
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def send_tx(w3, account, tx):
    nonce = w3.eth.get_transaction_count(account.address)
    tx.update({
        "from": account.address,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
        "gas": tx.get("gas", 700000),
        "maxFeePerGas": tx.get("maxFeePerGas", w3.to_wei(2, "gwei")),
        "maxPriorityFeePerGas": tx.get("maxPriorityFeePerGas", w3.to_wei(1, "gwei")),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def main():
    dep = load_json(DEPLOY_FILE)
    ar_art = load_json(AR_ART)
    cm_art = load_json(CM_ART)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Cannot connect to RPC: {RPC_URL}")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    ar = w3.eth.contract(
        address=Web3.to_checksum_address(dep["agentRegistry"]),
        abi=ar_art["abi"]
    )
    cm = w3.eth.contract(
        address=Web3.to_checksum_address(dep["capabilityManager"]),
        abi=cm_art["abi"]
    )

    out = {
        "network": NETWORK,
        "refreshedAt": int(time.time()),
        "ttlSeconds": TTL_SECONDS,
        "agents": []
    }

    for item in AGENTS:
        agent_id = item["agentId"]
        policy_class = item["policyClass"]
        scope_text = item["scopeText"]

        if not ar.functions.isRegistered(agent_id).call():
            raise RuntimeError(f"Agent not registered: {agent_id}")

        agent_key = ar.functions.agentKey(agent_id).call()
        scope_hash = w3.keccak(text=scope_text)
        capability_id = w3.keccak(text=f"{agent_id}:{policy_class}:{int(time.time())}")

        tx = cm.functions.issueCapability(
            capability_id,
            agent_key,
            scope_hash,
            policy_class,
            TTL_SECONDS
        ).build_transaction({"from": account.address})

        receipt = send_tx(w3, account, tx)
        valid = cm.functions.isValid(capability_id).call()

        out["agents"].append({
            "agentId": agent_id,
            "policyClass": policy_class,
            "capabilityId": capability_id.hex(),
            "capabilityValid": bool(valid),
            "txHash": receipt["transactionHash"].hex()
        })

        print(agent_id, "| new capability =", capability_id.hex(), "| valid =", bool(valid))

    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved ->", OUT_FILE)

if __name__ == "__main__":
    main()
