import json
from pathlib import Path
from web3 import Web3
from web3.exceptions import ContractLogicError

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
proof = json.load(open(ROOT / "artifacts" / "out_l4" / "zokrates_docker" / "proof.bad.json"))
circuit = json.load(open(ROOT / "artifacts" / "out_l4" / "circuit_input.auth_v1.json"))
artifact = json.load(open(ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorGroth16.sol" / "DecisionAttestorGroth16.json"))

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
account = w3.eth.account.from_key("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")

contract = w3.eth.contract(
    address=Web3.to_checksum_address(dep["decisionAttestorGroth16"]),
    abi=artifact["abi"],
)

raw = circuit["public_inputs_raw"]
runtime = circuit["runtime"]

a = [int(x, 16) for x in proof["proof"]["a"]]
b = [[int(x, 16) for x in row] for row in proof["proof"]["b"]]
c = [int(x, 16) for x in proof["proof"]["c"]]
inputs = [int(x, 16) for x in proof["inputs"]]

print("Wrapper ->", dep["decisionAttestorGroth16"])
print("Verifier ->", dep["authV1Groth16Verifier"])

try:
    result = contract.functions.submitDecision(
        runtime["agentId"],
        Web3.to_bytes(hexstr=raw["capabilityId"]),
        Web3.to_bytes(hexstr=raw["contextHash"]),
        Web3.to_bytes(hexstr=raw["traceCommitment"]),
        runtime["traceCID"],
        runtime["policyClass"],
        runtime["action"],
        int(raw["expiryBucket"]),
        a,
        b,
        c,
        inputs,
    ).call({"from": account.address, "gas": 12000000})
    print("Unexpected success ->", result)
except ContractLogicError as e:
    print("Expected submitDecision() rejection captured")
    print(e)
