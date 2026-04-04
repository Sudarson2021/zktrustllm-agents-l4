import json
from pathlib import Path
from web3 import Web3

ROOT = Path.cwd()

dep = json.load(open(ROOT / "deployments" / "l4.localhost.json"))
proof = json.load(open(ROOT / "artifacts" / "out_l4" / "zokrates_docker" / "proof.frozen.json"))
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
print("Input count ->", len(inputs))

preflight = contract.functions.submitDecision(
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

print("Preflight submitDecision() ->", preflight)

latest = w3.eth.get_block("latest")
base_fee = latest.get("baseFeePerGas", w3.to_wei(1, "gwei"))
priority_fee = w3.to_wei(1, "gwei")

tx = contract.functions.submitDecision(
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
).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address),
    "chainId": w3.eth.chain_id,
    "gas": 12000000,
    "maxFeePerGas": base_fee + priority_fee,
    "maxPriorityFeePerGas": priority_fee,
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

decision_count = contract.functions.decisionCount().call()
stored = contract.functions.decisions(decision_count).call()

print("Submitted Groth16 decision tx ->", receipt["transactionHash"].hex())
print("Decision count ->", decision_count)
print("Stored agentId ->", stored[0])
print("Stored policyClass ->", stored[5])
print("Stored action ->", stored[6])
print("Stored traceCID ->", stored[4])
print("Stored expiryBucket ->", stored[7])
