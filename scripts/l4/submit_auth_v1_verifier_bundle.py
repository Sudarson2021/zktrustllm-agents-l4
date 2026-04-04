import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

BUNDLE_FILE = ROOT / "artifacts" / "out_l4" / "verifier_bundle.auth_v1.json"
ATT_ART = ROOT / "artifacts" / "contracts" / "l4" / "DecisionAttestorZK.sol" / "DecisionAttestorZK.json"

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
    bundle = load_json(BUNDLE_FILE)
    att_art = load_json(ATT_ART)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    target = bundle["target"]
    sub = bundle["submission"]
    args = sub["args"]

    attestor = w3.eth.contract(
        address=Web3.to_checksum_address(target["contractAddress"]),
        abi=att_art["abi"]
    )

    tx = attestor.functions.submitAgentDecisionZK(
        args["agentId"],
        Web3.to_bytes(hexstr=args["capabilityIdHex"]),
        Web3.to_bytes(hexstr=args["contextHashHex"]),
        Web3.to_bytes(hexstr=args["traceCommitmentHex"]),
        args["traceCID"],
        args["policyClass"],
        args["action"],
        int(args["expiryBucket"]),
        Web3.to_bytes(hexstr=args["proofBlobHex"])
    ).build_transaction({"from": account.address, "gas": 1200000})

    receipt = send_tx(w3, account, tx)

    count = attestor.functions.zkDecisionCount().call()
    record = attestor.functions.zkDecisions(count).call()

    print("Submitted verifier-bundle ZK tx ->", receipt["transactionHash"].hex())
    print("ZK decision count ->", count)
    print("Stored decision agentId ->", record[0])
    print("Stored policyClass ->", record[5])
    print("Stored action ->", record[6])
    print("Stored traceCID ->", record[4])
    print("Stored expiryBucket ->", record[7])

if __name__ == "__main__":
    main()
