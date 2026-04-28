import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
payload = json.load(open(ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof_payload.auth_v2_1.frozen.json"))
proof = json.load(open(ROOT / "runtime_artifacts" / "l4" / "auth_v2_1" / "proof.frozen.json"))
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

preflight = contract.functions.submitDecision(
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

tx = contract.functions.submitDecision(
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
).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address),
    "gas": 5000000,
    "gasPrice": w3.eth.gas_price,
    "chainId": w3.eth.chain_id,
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

count = contract.functions.decisionCount().call()
stored = contract.functions.getDecision(count).call()

print("Wrapper ->", dep["decisionAttestorAuthV2_1"])
print("Verifier ->", dep["authV2_1Groth16Verifier"])
print("Input count ->", len(inputs))
print("Preflight submitDecision() ->", preflight)
print("Submitted AUTH_V2.1 decision tx ->", receipt["transactionHash"].hex())
print("Decision count ->", count)
print("Stored agentId ->", stored[0])
print("Stored capabilityId ->", stored[1].hex())
print("Stored policyClassHash ->", stored[2].hex())
print("Stored actionClass ->", stored[3])
print("Stored contextHash ->", stored[4].hex())
print("Stored traceCommitment ->", stored[5].hex())
print("Stored expiryBucket ->", stored[6])
print("Stored policyAdmissibilityFlag ->", stored[7])
