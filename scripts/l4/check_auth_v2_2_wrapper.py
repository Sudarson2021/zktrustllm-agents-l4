import json
from pathlib import Path
from web3 import Web3

root = Path.cwd()

dep = json.load(open(root / "deployments" / "l4.localhost.json"))
art = json.load(open(root / "artifacts" / "contracts" / "l4" / "DecisionAttestorAuthV2_2.sol" / "DecisionAttestorAuthV2_2.json"))
proof = json.load(open(root / "runtime_artifacts" / "l4" / "auth_v2_2" / "proof.frozen.json"))

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
ctt = w3.eth.contract(
    address=Web3.to_checksum_address(dep["decisionAttestorAuthV2_2"]),
    abi=art["abi"],
)

a = [int(x, 16) for x in proof["proof"]["a"]]
b = [[int(x, 16) for x in row] for row in proof["proof"]["b"]]
c = [int(x, 16) for x in proof["proof"]["c"]]
inputs = [int(x, 16) for x in proof["inputs"]]

print("Wrapper ->", dep["decisionAttestorAuthV2_2"])
print("Wrapper verifierAddress() ->", ctt.functions.verifierAddress().call())
print("Wrapper checkProof() ->", ctt.functions.checkProof(a, b, c, inputs).call({"gas": 12000000}))
