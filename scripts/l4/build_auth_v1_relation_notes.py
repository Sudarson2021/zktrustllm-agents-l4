import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_FILE = ROOT / "configs" / "l4" / "auth_v1_circuit_template.json"
WITNESS_FILE = ROOT / "artifacts" / "out_l4" / "witness_input.auth_v1.json"
OUT_FILE = ROOT / "artifacts" / "out_l4" / "relation_notes.auth_v1.v0.json"

CURRENT_CONSTRAINTS = [
    "all public binding fields are non-zero",
    "all key witness binding fields are non-zero and capabilitySalt is weakly anchored through saltAnchor = capabilitySalt + expiryBucket",
    "actionCode is bounded to the placeholder mitigation set 1..5",
    "agentKey != capabilityId",
    "agentKey != policyClassHash",
    "policyClassHash != actionHash",
    "contextHash != traceCommitment",
    "domainSepCapability != domainSepAction",
    "scopeHash != domainSepCapability",
    "scopeHash != domainSepAction",
    "expiryBucket > actionCode",
    "saltAnchor = capabilitySalt + expiryBucket and saltAnchor != 0",
]

NEXT_RELATION_TARGETS = [
    "bind capabilityId to a proof-native authorization relation",
    "bind actionHash to actionCode through a real hash relation",
    "bind capabilitySalt into a real authorization witness relation",
    "bind policy class to bounded action admissibility rules",
    "replace placeholder arithmetic relations with Groth16-verifiable constraints",
]

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    template = load_json(TEMPLATE_FILE)
    witness = load_json(WITNESS_FILE)

    out = {
        "schema": "auth_v1_relation_notes_v0",
        "version": "v0",
        "meta": {
            "taskId": witness["meta"]["taskId"],
            "targetAgent": witness["meta"]["targetAgent"],
            "traceCID": witness["meta"]["traceCID"],
            "sourceTemplateFile": str(TEMPLATE_FILE),
            "sourceWitnessFile": str(WITNESS_FILE),
        },
        "publicInputOrder": template["publicInputOrder"],
        "privateWitnessOrder": template["privateWitnessOrder"],
        "boundedActionMap": template["boundedActionMap"],
        "currentConstraints": CURRENT_CONSTRAINTS,
        "nextRelationTargets": NEXT_RELATION_TARGETS,
        "runtime": witness["runtime"],
        "status": {
            "stage": "relation_aware_v0",
            "proofReadiness": "still_placeholder_but_semantically_stronger",
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("Saved relation notes ->", OUT_FILE)
    print("Constraint count ->", len(CURRENT_CONSTRAINTS))

if __name__ == "__main__":
    main()
