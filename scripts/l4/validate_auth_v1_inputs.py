import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "configs" / "l4" / "test_vectors_auth_v1.json"

ACTION_CODES = {
    "keep": 1,
    "rekey": 2,
    "rotate": 3,
    "isolate": 4,
    "quarantine": 5,
}

REQUIRED_TOP = [
    "meta",
    "publicInputs",
    "witnessPlaceholders",
    "derivedDigests",
    "currentRuntimeValues",
]

REQUIRED_PUBLIC = [
    "agentKey",
    "capabilityId",
    "policyClassHash",
    "contextHash",
    "traceCommitment",
    "actionHash",
    "expiryBucket",
]

REQUIRED_WITNESS = [
    "scopeText",
    "scopeHash",
    "capabilitySalt",
    "actionCode",
    "domainSepCapability",
    "domainSepAction",
]

REQUIRED_DERIVED = [
    "capabilityWitnessDigestDraft",
    "actionWitnessDigestDraft",
    "publicInputDigest",
]

REQUIRED_RUNTIME = [
    "agentId",
    "policyClass",
    "action",
    "traceCID",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def norm32(x: str) -> str:
    x = x.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    if len(x) != 66:
        raise ValueError(f"Expected 32-byte hex value, got {x}")
    int(x[2:], 16)
    return x

def h(txt: str) -> str:
    return Web3.keccak(text=txt).hex()

def require_keys(obj, keys, name):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise KeyError(f"Missing keys in {name}: {missing}")

def main():
    data = load_json(INPUT_FILE)

    require_keys(data, REQUIRED_TOP, "top-level")
    require_keys(data["publicInputs"], REQUIRED_PUBLIC, "publicInputs")
    require_keys(data["witnessPlaceholders"], REQUIRED_WITNESS, "witnessPlaceholders")
    require_keys(data["derivedDigests"], REQUIRED_DERIVED, "derivedDigests")
    require_keys(data["currentRuntimeValues"], REQUIRED_RUNTIME, "currentRuntimeValues")

    pub = data["publicInputs"]
    wit = data["witnessPlaceholders"]
    dig = data["derivedDigests"]
    run = data["currentRuntimeValues"]

    # normalize 32-byte values
    pub["agentKey"] = norm32(pub["agentKey"])
    pub["capabilityId"] = norm32(pub["capabilityId"])
    pub["policyClassHash"] = norm32(pub["policyClassHash"])
    pub["contextHash"] = norm32(pub["contextHash"])
    pub["traceCommitment"] = norm32(pub["traceCommitment"])
    pub["actionHash"] = norm32(pub["actionHash"])

    wit["scopeHash"] = norm32(wit["scopeHash"])
    wit["capabilitySalt"] = norm32(wit["capabilitySalt"])
    wit["domainSepCapability"] = norm32(wit["domainSepCapability"])
    wit["domainSepAction"] = norm32(wit["domainSepAction"])

    dig["capabilityWitnessDigestDraft"] = norm32(dig["capabilityWitnessDigestDraft"])
    dig["actionWitnessDigestDraft"] = norm32(dig["actionWitnessDigestDraft"])
    dig["publicInputDigest"] = norm32(dig["publicInputDigest"])

    if run["action"] not in ACTION_CODES:
        raise ValueError(f"Unsupported runtime action: {run['action']}")

    expected_action_code = ACTION_CODES[run["action"]]
    if wit["actionCode"] != expected_action_code:
        raise ValueError(
            f"actionCode mismatch: expected {expected_action_code}, got {wit['actionCode']}"
        )

    expected_policy_hash = norm32(h(run["policyClass"]))
    expected_action_hash = norm32(h(run["action"]))
    expected_scope_hash = norm32(h(wit["scopeText"]))

    if pub["policyClassHash"] != expected_policy_hash:
        raise ValueError(
            f"policyClassHash mismatch: expected {expected_policy_hash}, got {pub['policyClassHash']}"
        )

    if pub["actionHash"] != expected_action_hash:
        raise ValueError(
            f"actionHash mismatch: expected {expected_action_hash}, got {pub['actionHash']}"
        )

    if wit["scopeHash"] != expected_scope_hash:
        raise ValueError(
            f"scopeHash mismatch: expected {expected_scope_hash}, got {wit['scopeHash']}"
        )

    public_input_digest = norm32(Web3.keccak(
        Web3().codec.encode(
            ["bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "bytes32", "uint256"],
            [
                Web3.to_bytes(hexstr=pub["agentKey"]),
                Web3.to_bytes(hexstr=pub["capabilityId"]),
                Web3.to_bytes(hexstr=pub["policyClassHash"]),
                Web3.to_bytes(hexstr=pub["contextHash"]),
                Web3.to_bytes(hexstr=pub["traceCommitment"]),
                Web3.to_bytes(hexstr=pub["actionHash"]),
                pub["expiryBucket"],
            ],
        )
    ).hex())

    if dig["publicInputDigest"] != public_input_digest:
        raise ValueError(
            f"publicInputDigest mismatch: expected {public_input_digest}, got {dig['publicInputDigest']}"
        )

    with open(INPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("AUTH_V1 inputs validated successfully")
    print("Normalized file ->", INPUT_FILE)
    print("publicInputDigest ->", public_input_digest)

if __name__ == "__main__":
    main()
