import json
import os
import time
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
NETWORK = os.getenv("L4_NETWORK", "localhost")
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")

# Hardhat local default account #0 private key (safe only for localhost dev)
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

TTL_SECONDS = int(os.getenv("L4_CAP_TTL", "3600"))

DEPLOY_FILE = ROOT / "deployments" / f"l4.{NETWORK}.json"
AGENT_REGISTRY_ARTIFACT = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"
CAPABILITY_MANAGER_ARTIFACT = ROOT / "artifacts" / "contracts" / "l4" / "CapabilityManager.sol" / "CapabilityManager.json"

OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / f"registered_agents.{NETWORK}.json"

AGENTS = [
    {
        "agentId": "edge-telemetry-01",
        "role": "EdgeTelemetryAgent",
        "modelClass": "telemetry",
        "trustTier": 1,
        "policyClass": "context-collect",
        "scopeText": "tenant-3:collect-context"
    },
    {
        "agentId": "trust-risk-01",
        "role": "TrustRiskAgent",
        "modelClass": "risk",
        "trustTier": 2,
        "policyClass": "risk-eval",
        "scopeText": "tenant-3:evaluate-risk"
    },
    {
        "agentId": "policy-lkh-01",
        "role": "PolicyLKHAgent",
        "modelClass": "policy",
        "trustTier": 3,
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
    if not DEPLOY_FILE.exists():
        raise FileNotFoundError(f"Missing deployment file: {DEPLOY_FILE}")

    deployment = load_json(DEPLOY_FILE)
    ar_artifact = load_json(AGENT_REGISTRY_ARTIFACT)
    cm_artifact = load_json(CAPABILITY_MANAGER_ARTIFACT)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Cannot connect to RPC: {RPC_URL}")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    agent_registry = w3.eth.contract(
        address=Web3.to_checksum_address(deployment["agentRegistry"]),
        abi=ar_artifact["abi"]
    )
    capability_manager = w3.eth.contract(
        address=Web3.to_checksum_address(deployment["capabilityManager"]),
        abi=cm_artifact["abi"]
    )

    results = {
        "network": NETWORK,
        "rpcUrl": RPC_URL,
        "admin": account.address,
        "registeredAt": int(time.time()),
        "agents": []
    }

    print("Connected to:", RPC_URL)
    print("Admin account:", account.address)
    print("AgentRegistry:", deployment["agentRegistry"])
    print("CapabilityManager:", deployment["capabilityManager"])
    print()

    for item in AGENTS:
        agent_id = item["agentId"]
        role = item["role"]
        model_class = item["modelClass"]
        trust_tier = item["trustTier"]
        policy_class = item["policyClass"]
        scope_text = item["scopeText"]

        pubkey_hash = w3.keccak(text=f"{agent_id}:pubkey")
        scope_hash = w3.keccak(text=scope_text)
        capability_id = w3.keccak(text=f"{agent_id}:{policy_class}:{int(time.time())}")

        print(f"Registering agent: {agent_id}")

        tx1 = agent_registry.functions.registerAgent(
            agent_id,
            account.address,
            pubkey_hash,
            role,
            model_class,
            trust_tier
        ).build_transaction({"from": account.address})
        receipt1 = send_tx(w3, account, tx1)

        agent_key = agent_registry.functions.agentKey(agent_id).call()

        print(f"Issuing capability: {policy_class}")

        tx2 = capability_manager.functions.issueCapability(
            capability_id,
            agent_key,
            scope_hash,
            policy_class,
            TTL_SECONDS
        ).build_transaction({"from": account.address})
        receipt2 = send_tx(w3, account, tx2)

        registered = agent_registry.functions.isRegistered(agent_id).call()
        capability_valid = capability_manager.functions.isValid(capability_id).call()
        capability_tuple = capability_manager.functions.getCapability(capability_id).call()

        result = {
            "agentId": agent_id,
            "role": role,
            "modelClass": model_class,
            "trustTier": trust_tier,
            "policyClass": policy_class,
            "scopeText": scope_text,
            "agentKey": agent_key.hex(),
            "pubKeyHash": pubkey_hash.hex(),
            "scopeHash": scope_hash.hex(),
            "capabilityId": capability_id.hex(),
            "registered": registered,
            "capabilityValid": capability_valid,
            "registerTx": receipt1["transactionHash"].hex(),
            "capabilityTx": receipt2["transactionHash"].hex(),
            "capabilityData": {
                "capabilityId": capability_tuple[0].hex(),
                "agentKey": capability_tuple[1].hex(),
                "scopeHash": capability_tuple[2].hex(),
                "policyClass": capability_tuple[3],
                "issuedAt": int(capability_tuple[4]),
                "expiresAt": int(capability_tuple[5]),
                "revoked": bool(capability_tuple[6]),
            }
        }

        results["agents"].append(result)

        print(f"  registered     : {registered}")
        print(f"  capabilityValid: {capability_valid}")
        print(f"  registerTx     : {result['registerTx']}")
        print(f"  capabilityTx   : {result['capabilityTx']}")
        print()

    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("Saved registration summary ->", OUT_FILE)

if __name__ == "__main__":
    main()
