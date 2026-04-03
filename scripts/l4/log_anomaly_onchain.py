import json
import os
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
RPC_URL = os.getenv("L4_RPC_URL", "http://127.0.0.1:8545")
DEFAULT_LOCAL_PK = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ADMIN_PRIVATE_KEY = os.getenv("L4_ADMIN_PRIVATE_KEY", DEFAULT_LOCAL_PK)

DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
LEDGER_ART = ROOT / "artifacts" / "contracts" / "l4" / "AnomalyLedger.sol" / "AnomalyLedger.json"
ANOM_FILE = ROOT / "artifacts" / "out_l4" / "traces" / "anomaly_bundle.task-0001.json"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def send_tx(w3, account, tx):
    nonce = w3.eth.get_transaction_count(account.address)
    tx.update({
        "from": account.address,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
        "gas": tx.get("gas", 500000),
        "maxFeePerGas": tx.get("maxFeePerGas", w3.to_wei(2, "gwei")),
        "maxPriorityFeePerGas": tx.get("maxPriorityFeePerGas", w3.to_wei(1, "gwei")),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def main():
    dep = load_json(DEPLOY_FILE)
    ledger_art = load_json(LEDGER_ART)
    anomaly = load_json(ANOM_FILE)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to local chain")

    account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

    ledger = w3.eth.contract(
        address=Web3.to_checksum_address(dep["anomalyLedger"]),
        abi=ledger_art["abi"]
    )

    tx = ledger.functions.logAnomaly(
        "edge-telemetry-01",
        anomaly["severity"],
        anomaly["linkedTraceCID"],
        Web3.to_bytes(hexstr=anomaly["anomalyCommitment"])
    ).build_transaction({"from": account.address})

    receipt = send_tx(w3, account, tx)

    count = ledger.functions.anomalyCount().call()
    record = ledger.functions.anomalies(count).call()

    print("Logged anomaly tx ->", receipt["transactionHash"].hex())
    print("Anomaly count ->", count)
    print("Stored agentId ->", record[0])
    print("Stored severity ->", record[1])
    print("Stored traceCID ->", record[2])
    print("Stored commitment ->", record[3].hex())

if __name__ == "__main__":
    main()
