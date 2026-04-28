import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
payload = json.load(open(ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof_payload.auth_v2_1.frozen.json"))
proof = json.load(open(ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof.bad.json"))
artifact = json.load(open(ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorAuthV2_1.sol" / "DecisionAttestorAuthV2_1.json"))

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

def int_to_bytes32(value: int) -> bytes:
    return int(value).to_bytes(32, byteorder="big")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(dep["decisionAttestorAuthV2_1"]),
    abi=artifact["abi"],
)

a = [int(x, 16) for x in proof["proof"]["a"]]
b = [[int(x, 16) for x in row] for row in proof["proof"]["b"]]
c = [int(x, 16) for x in proof["proof"]["c"]]
inputs = [int(x, 16) for x in proof["inputs"]]

try:
    contract.functions.submitDecision(
        payload["agentId"],
        int_to_bytes32(payload["capabilityId"]),
        int_to_bytes32(payload["policyClassHash"]),
        int(payload["actionClass"]),
        int_to_bytes32(payload["contextHash"]),
        int_to_bytes32(payload["traceCommitment"]),
        int(payload["expiryBucket"]),
        int(payload["policyAdmissibilityFlag"]),
        a,
        b,
        c,
        inputs,
    ).call({"from": account.address})

    print("Unexpected submitDecision() success")
except Exception as e:
    print("Expected submitDecision() rejection captured")
    print(e)
