import json
from pathlib import Path
from web3 import Web3
from web3.exceptions import ContractLogicError

root = Path.cwd()

dep = json.load(open(root / "deployments" / "l4.localhost.json"))
art = json.load(open(root / "artifacts" / "contracts" / "l4" / "DecisionAttestorGroth16.sol" / "DecisionAttestorGroth16.json"))
proof = json.load(open(root / "artifacts" / "out_l4" / "zokrates_docker" / "proof.bad.json"))

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
ctt = w3.eth.contract(
    address=Web3.to_checksum_address(dep["decisionAttestorGroth16"]),
    abi=art["abi"],
)

a = [int(x, 16) for x in proof["proof"]["a"]]
b = [[int(x, 16) for x in row] for row in proof["proof"]["b"]]
c = [int(x, 16) for x in proof["proof"]["c"]]
inputs = [int(x, 16) for x in proof["inputs"]]

print("Wrapper ->", dep["decisionAttestorGroth16"])
print("Wrapper verifierAddress() ->", ctt.functions.verifierAddress().call())

try:
    result = ctt.functions.checkProof(a, b, c, inputs).call({"gas": 12000000})
    print("Bad proof checkProof() ->", result)
    if result is True:
        raise SystemExit("Unexpected wrapper acceptance")
    print("Expected wrapper rejection captured")
except ContractLogicError as e:
    print("Expected wrapper rejection captured")
    print(e)
