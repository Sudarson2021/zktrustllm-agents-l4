#!/usr/bin/env python3

import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_mcp_a2a_security"
OUT_FILE = OUT_DIR / "mcp_a2a_negative_summary.json"


def extract_text(result):
    if not result.content:
        return ""
    item = result.content[0]
    return getattr(item, "text", str(item))


async def call_tool(session, tool_name, arguments):
    start = time.perf_counter()
    result = await session.call_tool(tool_name, arguments)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    text = extract_text(result)
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {"rawText": text}

    return {
        "tool": tool_name,
        "arguments": arguments,
        "latencyMs": latency_ms,
        "result": parsed,
    }


async def main():
    server_script = ROOT / "mcp_l4" / "server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tests = []

            invalid_decision = await call_tool(
                session,
                "get_auth_v2_2_decision",
                {"decision_id": 999}
            )
            tests.append({
                "name": "invalid_auth_v2_2_decision_lookup",
                "expected": "MCP tool returns ok=false for out-of-range decision",
                "call": invalid_decision,
                "passed": invalid_decision["result"].get("ok") is False,
            })

            invalid_reference = await call_tool(
                session,
                "get_a2a_reference",
                {"reference_id": 999}
            )
            tests.append({
                "name": "invalid_a2a_reference_lookup",
                "expected": "MCP tool returns ok=false for out-of-range reference",
                "call": invalid_reference,
                "passed": invalid_reference["result"].get("ok") is False,
            })

            invalid_reference_validity = await call_tool(
                session,
                "is_a2a_reference_valid",
                {"reference_id": 999}
            )
            tests.append({
                "name": "invalid_a2a_reference_validity_check",
                "expected": "MCP validity tool returns valid=false for out-of-range reference",
                "call": invalid_reference_validity,
                "passed": (
                    invalid_reference_validity["result"].get("ok") is True
                    and invalid_reference_validity["result"].get("valid") is False
                ),
            })

            invalid_bundle = await call_tool(
                session,
                "verify_reference_bundle",
                {"reference_id": 999}
            )
            tests.append({
                "name": "invalid_reference_bundle_verification",
                "expected": "MCP bundle verifier returns ok=false for invalid reference",
                "call": invalid_bundle,
                "passed": invalid_bundle["result"].get("ok") is False,
            })

            total = len(tests)
            passed = sum(1 for t in tests if t["passed"])
            rejection_rate = passed / total if total else 0

            output = {
                "experiment": "mcp_a2a_negative_security_tests",
                "negativeCaseCount": total,
                "negativeCasesPassed": passed,
                "mcpA2AInvalidContextRejectionRate": rejection_rate,
                "tests": tests,
            }

            OUT_DIR.mkdir(parents=True, exist_ok=True)
            OUT_FILE.write_text(json.dumps(output, indent=2) + "\n")

            print(json.dumps(output, indent=2))
            print(f"Saved: {OUT_FILE}")

            if rejection_rate != 1:
                raise SystemExit("MCP/A2A negative-security tests did not fully pass")


if __name__ == "__main__":
    asyncio.run(main())
