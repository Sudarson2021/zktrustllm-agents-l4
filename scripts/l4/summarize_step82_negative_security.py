#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AUTH_NEG = ROOT / "results" / "l4_auth_v2_3_negative" / "auth_v2_3_negative_summary.json"
MCP_NEG = ROOT / "results" / "l4_mcp_a2a_security" / "mcp_a2a_negative_summary.json"
OUT_DIR = ROOT / "results" / "l4_mcp_a2a_security"
OUT = OUT_DIR / "step82_negative_security_summary.md"

auth = json.loads(AUTH_NEG.read_text())
mcp = json.loads(MCP_NEG.read_text())

lines = [
    "# Step 82 Negative Security Summary",
    "",
    "## AUTH_V2.3 Negative Security",
    "",
    f"- Negative cases: {auth['negativeCaseCount']}",
    f"- Passed negative cases: {auth['negativeCasesPassed']}",
    f"- Unauthorized/tampered rejection rate: {auth['unauthorizedOrTamperedRejectionRate']}",
    "",
    "## MCP/A2A Invalid Context Security",
    "",
    f"- Negative cases: {mcp['negativeCaseCount']}",
    f"- Passed negative cases: {mcp['negativeCasesPassed']}",
    f"- Invalid-context rejection rate: {mcp['mcpA2AInvalidContextRejectionRate']}",
    "",
    "## Interpretation",
    "",
    "The Level 4 design accepts the valid AUTH_V2.3 reference-bound proof path and rejects tampered proof inputs, malformed verifier inputs, invalid decision lookups, and invalid A2A reference contexts.",
]

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n")

print(OUT.read_text())
print(f"Saved: {OUT}")
