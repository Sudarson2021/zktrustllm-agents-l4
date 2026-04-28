import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
payload = json.load(open(ROOT / "artifacts" / "out_l4" / "proof_payload.auth_v2.frozen.json"))
proof = json.load(open(ROOT / "artifacts" / "out_l4" / "zokrates_docker_auth_v2" / "proof.frozen.json"))
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

agent_id = payload["agentId"]
capability_id = int_to_bytes32(payload["capabilityId"])
policy_class_hash = int_to_bytes32(payload["policyClassHash"])
action_class = int(payload["actionClass"])
context_hash = int_to_bytes32(payload["contextHash"])
trace_commitment = int_to_bytes32(payload["traceCommitment"])
expiry_bucket = int(payload["expiryBucket"])

preflight = contract.functions.submitDecision(
    agent_id,
    capability_id,
    policy_class_hash,
    action_class,
    context_hash,
    trace_commitment,
    expiry_bucket,
    a,
    b,
    c,
    inputs,
).call({"from": account.address})

tx = contract.functions.submitDecision(
    agent_id,
    capability_id,
    policy_class_hash,
    action_class,
    context_hash,
    trace_commitment,
    expiry_bucket,
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

print("Wrapper ->", dep["decisionAttestorAuthV2"])
print("Verifier ->", dep["authV2Groth16Verifier"])
print("Input count ->", len(inputs))
print("Preflight submitDecision() ->", preflight)
print("Submitted AUTH_V2 decision tx ->", receipt["transactionHash"].hex())
print("Decision count ->", count)
print("Stored agentId ->", stored[0])
print("Stored capabilityId ->", stored[1].hex())
print("Stored policyClassHash ->", stored[2].hex())
print("Stored actionClass ->", stored[3])
print("Stored contextHash ->", stored[4].hex())
print("Stored traceCommitment ->", stored[5].hex())
print("Stored expiryBucket ->", stored[6])
