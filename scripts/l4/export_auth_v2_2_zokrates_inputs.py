import json
from pathlib import Path

ROOT = Path.cwd()
OUT_DIR = ROOT / "artifacts" / "out_l4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CIRCUIT_INPUT_FILE = OUT_DIR / "circuit_input.auth_v2_2.json"
ZOKRATES_JSON_FILE = OUT_DIR / "zokrates_input.auth_v2_2.json"
FLAT_ARGS_FILE = OUT_DIR / "auth_v2_2.flat_args.txt"

def main():
    with open(CIRCUIT_INPUT_FILE, "r") as f:
        data = json.load(f)

    public_order = data["publicInputOrder"]
    public_inputs = data["publicInputs"]
    private_inputs = data["privateInputs"]

    flat_args = [str(private_inputs["bindingNonce"])]
    for key in public_order:
        flat_args.append(str(public_inputs[key]))

    out = {
        "scheme": "auth_v2_2",
        "relationVersion": data["relationVersion"],
        "flatArguments": flat_args,
        "argumentCount": len(flat_args),
        "privateArgumentOrder": ["bindingNonce"],
        "publicArgumentOrder": public_order,
    }

    with open(ZOKRATES_JSON_FILE, "w") as f:
        json.dump(out, f, indent=2)

    FLAT_ARGS_FILE.write_text(" ".join(flat_args))

    print("Saved AUTH_V2.2 ZoKrates input ->", ZOKRATES_JSON_FILE)
    print("Saved AUTH_V2.2 flat args    ->", FLAT_ARGS_FILE)
    print("Argument count ->", len(flat_args))
    print("Private arg order ->", out["privateArgumentOrder"])
    print("Public arg order ->", out["publicArgumentOrder"])

if __name__ == "__main__":
    main()
