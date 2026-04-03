import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = "http://127.0.0.1:8545"

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
AR_ART = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"
CM_ART = ROOT / "artifacts" / "contracts" / "l4" / "CapabilityManager.sol" / "CapabilityManager.json"

OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "registered_agents.localhost.json"

AGENTS = [
    "edge-telemetry-01",
    "trust-risk-01",
    "policy-lkh-01",
]

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Cannot connect to local chain: {RPC_URL}")

    dep = load_json(DEPLOY_FILE)
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

    agent_keys = {}
    for agent_id in AGENTS:
        agent_keys[agent_id] = ar.functions.agentKey(agent_id).call().hex()

    # Pull all CapabilityIssued events and keep the latest per agentKey
    latest_capability_by_agent_key = {}
    events = cm.events.CapabilityIssued().get_logs(from_block=0, to_block='latest')

    for ev in events:
        capability_id = ev["args"]["capabilityId"].hex()
        agent_key = ev["args"]["agentKey"].hex()
        policy_class = ev["args"]["policyClass"]
        expires_at = int(ev["args"]["expiresAt"])
        block_number = int(ev["blockNumber"])

        prev = latest_capability_by_agent_key.get(agent_key)
        if prev is None or block_number >= prev["blockNumber"]:
            latest_capability_by_agent_key[agent_key] = {
                "capabilityId": capability_id,
                "agentKey": agent_key,
                "policyClass": policy_class,
                "expiresAt": expires_at,
                "blockNumber": block_number,
            }

    out = {
        "network": "localhost",
        "agentRegistry": dep["agentRegistry"],
        "capabilityManager": dep["capabilityManager"],
        "agents": []
    }

    for agent_id in AGENTS:
        registered = bool(ar.functions.isRegistered(agent_id).call())
        agent_key = agent_keys[agent_id]

        item = {
            "agentId": agent_id,
            "registered": registered,
            "agentKey": agent_key,
        }

        latest = latest_capability_by_agent_key.get(agent_key)
        if latest is not None:
            cap_id_hex = latest["capabilityId"]
            cap_tuple = cm.functions.getCapability(Web3.to_bytes(hexstr=cap_id_hex)).call()
            valid = bool(cm.functions.isValid(Web3.to_bytes(hexstr=cap_id_hex)).call())

            item.update({
                "capabilityId": cap_tuple[0].hex(),
                "capabilityValid": valid,
                "scopeHash": cap_tuple[2].hex(),
                "policyClass": cap_tuple[3],
                "issuedAt": int(cap_tuple[4]),
                "expiresAt": int(cap_tuple[5]),
                "revoked": bool(cap_tuple[6]),
            })
        else:
            item.update({
                "capabilityId": None,
                "capabilityValid": False,
                "scopeHash": None,
                "policyClass": None,
                "issuedAt": None,
                "expiresAt": None,
                "revoked": None,
            })

        out["agents"].append(item)

    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved ->", OUT_FILE)

if __name__ == "__main__":
    main()
