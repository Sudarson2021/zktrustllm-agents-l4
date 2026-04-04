import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parents[2]

PROOF_JSON = ROOT / "artifacts" / "out_l4" / "zokrates_docker" / "proof.json"
CIRCUIT_INPUT = ROOT / "artifacts" / "out_l4" / "circuit_input.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.real.json"

BN128_SCALAR_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617

PUBLIC_ORDER = [
    "agentKey",
    "capabilityId",
    "policyClassHash",
    "contextHash",
    "traceCommitment",
    "actionHash",
    "expiryBucket",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def norm_hex(x: str) -> str:
    x = x.lower()
    if not x.startswith("0x"):
        x = "0x" + x
    return x

def int_to_hex(x: int) -> str:
    return hex(x)

def main():
    proof = load_json(PROOF_JSON)
    circuit = load_json(CIRCUIT_INPUT)

    raw_public = circuit["public_inputs_raw"]

    expected_inputs_hex = []
    expected_inputs_dec = []

    for name in PUBLIC_ORDER:
        value = raw_public[name]
        if name == "expiryBucket":
            n = int(value)
        else:
            n = int(norm_hex(value), 16)

        reduced = n % BN128_SCALAR_FIELD
        expected_inputs_dec.append(str(reduced))
        expected_inputs_hex.append(norm_hex(int_to_hex(reduced)))

    actual_inputs_hex = [norm_hex(x) for x in proof["inputs"]]
    actual_inputs_dec = [str(int(norm_hex(x), 16)) for x in proof["inputs"]]

    if len(actual_inputs_hex) != len(expected_inputs_hex):
        raise ValueError(
            f"ZoKrates input count mismatch: {len(actual_inputs_hex)} vs {len(expected_inputs_hex)}"
        )

    for i, (exp_h, got_h) in enumerate(zip(expected_inputs_hex, actual_inputs_hex)):
        if int(exp_h, 16) != int(got_h, 16):
            raise ValueError(
                f"Public input mismatch at index {i} ({PUBLIC_ORDER[i]}): expected {exp_h}, got {got_h}"
            )

    digest_material = json.dumps(
        {
            "scheme": proof["scheme"],
            "curve": proof["curve"],
            "proof": proof["proof"],
            "inputs": actual_inputs_hex,
        },
        sort_keys=True,
    ).encode()

    proof_digest = norm_hex(Web3.keccak(digest_material).hex())

    out = {
        "schema": "auth_v1_real_proof_output",
        "meta": {
            "taskId": circuit["meta"]["taskId"],
            "targetAgent": circuit["meta"]["targetAgent"],
            "traceCID": circuit["meta"]["traceCID"],
            "sourceProofJsonFile": str(PROOF_JSON),
            "sourceCircuitInputFile": str(CIRCUIT_INPUT),
        },
        "proofSystem": {
            "backend": "zokrates",
            "scheme": proof["scheme"],
            "curve": proof["curve"],
        },
        "publicInputOrder": PUBLIC_ORDER,
        "publicInputsRawHex": {
            k: (raw_public[k] if k == "expiryBucket" else norm_hex(raw_public[k]))
            for k in PUBLIC_ORDER
        },
        "publicInputsFieldHex": {
            k: actual_inputs_hex[i] for i, k in enumerate(PUBLIC_ORDER)
        },
        "publicInputsFieldDec": {
            k: actual_inputs_dec[i] for i, k in enumerate(PUBLIC_ORDER)
        },
        "proof": {
            "a": [norm_hex(x) for x in proof["proof"]["a"]],
            "b": [[norm_hex(x) for x in row] for row in proof["proof"]["b"]],
            "c": [norm_hex(x) for x in proof["proof"]["c"]],
            "inputs": actual_inputs_hex,
        },
        "derived": {
            "bn128ScalarField": str(BN128_SCALAR_FIELD),
            "publicInputDigest": norm_hex(circuit["derivedDigests"]["publicInputDigest"]),
            "proofDigest": proof_digest,
            "proofInputsValidated": True,
            "note": "ZoKrates proof inputs are field-reduced modulo the BN128 scalar field",
        },
        "runtime": circuit["runtime"],
        "compatibility": {
            "currentMockVerifierCompatible": False,
            "reason": "current deployed DecisionAttestorZK path still expects mock digest-style proofBlobHex",
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved real proof output ->", OUT_FILE)
    print("proofDigest ->", proof_digest)
    print("Validated public inputs ->", len(actual_inputs_hex))

if __name__ == "__main__":
    main()
