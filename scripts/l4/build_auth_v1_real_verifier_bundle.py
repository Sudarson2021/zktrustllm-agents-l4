import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REAL_PROOF_FILE = ROOT / "artifacts" / "out_l4" / "proof_output.auth_v1.real.json"
DEPLOY_FILE = ROOT / "deployments" / "l4.localhost.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "verifier_bundle.auth_v1.real.json"

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    real = load_json(REAL_PROOF_FILE)
    dep = load_json(DEPLOY_FILE)

    runtime = real["runtime"]
    raw = real["publicInputsRawHex"]
    field_hex = real["publicInputsFieldHex"]

    out = {
        "schema": "auth_v1_real_verifier_bundle",
        "meta": {
            "taskId": real["meta"]["taskId"],
            "targetAgent": real["meta"]["targetAgent"],
            "traceCID": real["meta"]["traceCID"],
            "sourceRealProofFile": str(REAL_PROOF_FILE),
        },
        "target": {
            "network": "localhost",
            "currentWrapperContract": "DecisionAttestorZK",
            "currentWrapperAddress": dep.get("decisionAttestorZK"),
            "currentSubmissionSupported": False,
            "currentReason": "deployed wrapper still uses mock structured-digest verifier semantics, not Groth16 proof point verification",
            "nextRequiredTarget": "Groth16-capable wrapper/verifier deployment",
        },
        "proofSystem": real["proofSystem"],
        "publicInputOrder": real["publicInputOrder"],
        "zokratesProof": {
            "a": real["proof"]["a"],
            "b": real["proof"]["b"],
            "c": real["proof"]["c"],
            "inputs": real["proof"]["inputs"],
        },
        "runtimeArgs": {
            "agentId": runtime["agentId"],
            "capabilityIdHex": raw["capabilityId"],
            "contextHashHex": raw["contextHash"],
            "traceCommitmentHex": raw["traceCommitment"],
            "traceCID": runtime["traceCID"],
            "policyClass": runtime["policyClass"],
            "action": runtime["action"],
            "expiryBucket": int(raw["expiryBucket"]),
        },
        "futureGroth16SubmissionShape": {
            "methodConcept": "wrapper-specific Groth16 submit path",
            "requiredArgs": [
                "agentId",
                "capabilityIdHex",
                "contextHashHex",
                "traceCommitmentHex",
                "traceCID",
                "policyClass",
                "action",
                "expiryBucket",
                "proof.a",
                "proof.b",
                "proof.c",
                "publicInputs",
            ],
        },
        "derived": {
            "proofDigest": real["derived"]["proofDigest"],
            "publicInputDigest": real["derived"]["publicInputDigest"],
            "fieldReducedInputs": field_hex,
        },
        "status": {
            "readyForCurrentDeployedContract": False,
            "readyForFutureGroth16Wrapper": True,
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved real verifier bundle ->", OUT_FILE)
    print("Current deployed contract compatible ->", out["status"]["readyForCurrentDeployedContract"])
    print("Future Groth16 wrapper ready ->", out["status"]["readyForFutureGroth16Wrapper"])

if __name__ == "__main__":
    main()
