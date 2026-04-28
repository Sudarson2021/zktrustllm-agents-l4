import json
from pathlib import Path
from web3 import Web3
from web3.exceptions import ContractLogicError

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
payload = json.load(open(ROOT / "artifacts" / "out_l4" / "proof_payload.auth_v2.frozen.json"))
proof = json.load(open(ROOT / "artifacts" / "out_l4" / "zokrates_docker_auth_v2" / "proof.bad.json"))
artifact = json.load(open(ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorAuthV2.sol" / "DecisionAttestorAuthV2.json"))

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

def int_to_bytes32(value: int) -> bytes:
    return int(value).to_bytes(32, byteorder="big")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(dep["decisionAttestorAuthV2"]),
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
        a,
        b,
        c,
        inputs,
    ).call({"from": account.address})

    print("Unexpected success: bad AUTH_V2 proof was accepted")
except ContractLogicError as e:
    print("Expected submitDecision() rejection captured")
    print(e)
