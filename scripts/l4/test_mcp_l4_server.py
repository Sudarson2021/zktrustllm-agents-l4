#!/usr/bin/env python3

import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "l4_mcp_server"
OUT_FILE = OUT_DIR / "mcp_tool_test_results.json"


def _extract_text(result):
    if not result.content:
        return ""
    item = result.content[0]
    return getattr(item, "text", str(item))


async def call_tool(session, tool_name, arguments):
    start = time.perf_counter()
    result = await session.call_tool(tool_name, arguments)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    text = _extract_text(result)
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

            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            calls = []
            calls.append(await call_tool(session, "get_auth_v2_2_decision", {"decision_id": 1}))
            calls.append(await call_tool(session, "get_a2a_reference", {"reference_id": 1}))
            calls.append(await call_tool(session, "is_a2a_reference_valid", {"reference_id": 1}))
            calls.append(await call_tool(session, "verify_reference_bundle", {"reference_id": 1}))
            calls.append(await call_tool(session, "get_level4_kpi_summary", {}))

            success_count = sum(1 for c in calls if c["result"].get("ok") is True)
            total_count = len(calls)
            success_rate = success_count / total_count if total_count else 0.0

            latencies = [c["latencyMs"] for c in calls]
            avg_latency = round(sum(latencies) / len(latencies), 3)
            max_latency = round(max(latencies), 3)

            output = {
                "mcpServer": "ZKTrustLLM-Level4-MCP",
                "listedTools": tool_names,
                "toolCallCount": total_count,
                "successfulToolCalls": success_count,
                "mcpContextRetrievalSuccessRate": success_rate,
                "averageToolInvocationLatencyMs": avg_latency,
                "maxToolInvocationLatencyMs": max_latency,
                "calls": calls,
            }

            OUT_DIR.mkdir(parents=True, exist_ok=True)
            OUT_FILE.write_text(json.dumps(output, indent=2) + "\n")

            print(json.dumps(output, indent=2))
            print(f"Saved: {OUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
