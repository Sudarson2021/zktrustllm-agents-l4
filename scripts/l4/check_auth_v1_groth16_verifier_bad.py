import json
from pathlib import Path
from web3 import Web3
from web3.exceptions import ContractLogicError

root = Path.cwd()

dep = json.load(open(root / "deployments" / "l4.localhost.json"))
art = json.load(open(root / "artifacts" / "contracts" / "l4" / "generated" / "AuthV1Verifier.sol" / "Verifier.json"))
proof = json.load(open(root / "artifacts" / "out_l4" / "zokrates_docker" / "proof.bad.json"))

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
v = w3.eth.contract(
    address=Web3.to_checksum_address(dep["authV1Groth16Verifier"]),
    abi=art["abi"],
)

a = [int(x, 16) for x in proof["proof"]["a"]]
b = [[int(x, 16) for x in row] for row in proof["proof"]["b"]]
c = [int(x, 16) for x in proof["proof"]["c"]]
inputs = [int(x, 16) for x in proof["inputs"]]

print("Verifier ->", dep["authV1Groth16Verifier"])

try:
    result = v.functions.verifyTx((a, b, c), inputs).call()
    print("Bad proof verifyTx ->", result)
    if result is True:
        raise SystemExit("Unexpected verifier acceptance")
    print("Expected direct verifier rejection captured")
except ContractLogicError as e:
    print("Expected direct verifier rejection captured")
    print(e)
