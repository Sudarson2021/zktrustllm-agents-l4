import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorZK.sol" / "DecisionAttestorZK.json"
PROOF_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.mock.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def send_tx(w3, account, tx):
    nonce = w3.eth.get_transaction_count(account.address)
    tx.update({
        "from": account.address,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
        "gas": tx.get("gas", 1200000),
        "maxFeePerGas": tx.get("maxFeePerGas", w3.to_wei(2, "gwei")),
        "maxPriorityFeePerGas": tx.get("maxPriorityFeePerGas", w3.to_wei(1, "gwei")),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def main():
    dep = load_json(DEPLOY_FILE)
    att_art = load_json(ATT_ART)
    proof = load_json(PROOF_FILE)

    if "decisionAttestorZKV2" not in dep:
        raise RuntimeError("decisionAttestorZKV2 not found in deployments")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(dep["decisionAttestorZKV2"]),
        abi=att_art["abi"]
    )

    pub = proof["publicInputsRaw"]
    runtime = proof["runtime"]
    proof_blob_hex = proof["proof"]["proofBlobHex"]

    tx = attestor.functions.submitAgentDecisionZK(
        runtime["agentId"],
        Web3.to_bytes(hexstr=pub["capabilityId"]),
        Web3.to_bytes(hexstr=pub["contextHash"]),
        Web3.to_bytes(hexstr=pub["traceCommitment"]),
        runtime["traceCID"],
        runtime["policyClass"],
        runtime["action"],
        int(pub["expiryBucket"]),
        Web3.to_bytes(hexstr=proof_blob_hex)
    ).build_transaction({"from": account.address, "gas": 1200000})

    receipt = send_tx(w3, account, tx)

    count = attestor.functions.zkDecisionCount().call()
    record = attestor.functions.zkDecisions(count).call()

    print("Submitted proof-output-based ZK tx ->", receipt["transactionHash"].hex())
    print("ZK decision count ->", count)
    print("Stored decision agentId ->", record[0])
    print("Stored policyClass ->", record[5])
    print("Stored action ->", record[6])
    print("Stored traceCID ->", record[4])
    print("Stored expiryBucket ->", record[7])

if __name__ == "__main__":
    main()
