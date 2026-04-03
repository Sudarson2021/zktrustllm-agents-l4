import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
NETWORK = os.getenv("L4_NETWORK", "localhost")
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")

DEPLOY_FILE = ROOT / "deployments" / f"l4.{NETWORK}.json"
AGENT_REGISTRY_ARTIFACT = ROOT / "artifacts" / "contracts" / "l4" / "AgentRegistry.sol" / "AgentRegistry.json"
CAPABILITY_MANAGER_ARTIFACT = ROOT / "artifacts" / "contracts" / "l4" / "CapabilityManager.sol" / "CapabilityManager.json"

def _load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def _ensure_0x(hex_str: str) -> str:
    if hex_str.startswith("0x") or hex_str.startswith("0X"):
        return hex_str
    return "0x" + hex_str

def _norm_hex(hex_str: str) -> str:
    return _ensure_0x(hex_str).lower()

class ChainGuard:
    def __init__(self):
        if not DEPLOY_FILE.exists():
            raise FileNotFoundError(f"Missing deployment file: {DEPLOY_FILE}")

        deployment = _load_json(DEPLOY_FILE)
        ar_artifact = _load_json(AGENT_REGISTRY_ARTIFACT)
        cm_artifact = _load_json(CAPABILITY_MANAGER_ARTIFACT)

        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise RuntimeError(f"Cannot connect to RPC: {RPC_URL}")

        self.agent_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(deployment["agentRegistry"]),
            abi=ar_artifact["abi"]
        )
        self.capability_manager = self.w3.eth.contract(
            address=Web3.to_checksum_address(deployment["capabilityManager"]),
            abi=cm_artifact["abi"]
        )

    def is_registered(self, agent_id: str) -> bool:
        return bool(self.agent_registry.functions.isRegistered(agent_id).call())

    def agent_key(self, agent_id: str) -> str:
        return _norm_hex(self.agent_registry.functions.agentKey(agent_id).call().hex())

    def capability_valid(self, capability_id_hex: str) -> bool:
        cap_id = self.w3.to_bytes(hexstr=_ensure_0x(capability_id_hex))
        return bool(self.capability_manager.functions.isValid(cap_id).call())

    def get_capability(self, capability_id_hex: str):
        cap_id = self.w3.to_bytes(hexstr=_ensure_0x(capability_id_hex))
        c = self.capability_manager.functions.getCapability(cap_id).call()
        return {
            "capabilityId": _norm_hex(c[0].hex()),
            "agentKey": _norm_hex(c[1].hex()),
            "scopeHash": _norm_hex(c[2].hex()),
            "policyClass": c[3],
            "issuedAt": int(c[4]),
            "expiresAt": int(c[5]),
            "revoked": bool(c[6]),
        }
