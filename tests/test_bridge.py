"""Tests for plugins/game-maker-agent/mcp/unreal_bridge.py that need no Unreal Editor.

They check the MCP conversation (initialize, tools/list, errors) with any Python 3.
No model calls; free to run.
Usage: python tests/test_bridge.py
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, "..", "plugins", "game-maker-agent", "mcp", "unreal_bridge.py")

EXPECTED_TOOLS = {
    "unreal_status",
    "unreal_list_assets",
    "unreal_list_level_actors",
    "unreal_get_properties",
    "unreal_run_python",
}


def converse(requests):
    env = dict(os.environ)
    env.pop("GMA_UE_ENGINE_DIR", None)
    lines = "".join(json.dumps(r) + "\n" for r in requests)
    done = subprocess.run([sys.executable, "-I", "-u", BRIDGE], input=lines, capture_output=True, text=True, timeout=60, env=env)
    return {m["id"]: m for m in (json.loads(l) for l in done.stdout.splitlines() if l.strip())}


def main():
    replies = converse([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "unreal_get_properties", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "no_such_tool", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 5, "method": "no/such/method"},
        {"jsonrpc": "2.0", "id": 6, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}},
    ])
    checks = [
        ("initialize answers with the requested protocol", replies[1]["result"]["protocolVersion"] == "2025-06-18"),
        ("notifications get no reply", set(replies) == {1, 2, 3, 4, 5, 6}),
        ("all tools are listed", {t["name"] for t in replies[2]["result"]["tools"]} == EXPECTED_TOOLS),
        ("tools have input schemas", all("inputSchema" in t for t in replies[2]["result"]["tools"])),
        ("run_python is the only tool that isn't read-only",
         [t["name"] for t in replies[2]["result"]["tools"] if not t["annotations"]["readOnlyHint"]] == ["unreal_run_python"]),
        ("a missing argument is a tool error, not a crash", replies[3]["result"]["isError"] is True),
        ("an unknown tool is a JSON-RPC error", "error" in replies[4]),
        ("an unknown method is a JSON-RPC error", replies[5]["error"]["code"] == -32601),
        ("an unknown protocol falls back to a supported one", replies[6]["result"]["protocolVersion"] == "2025-06-18"),
    ]
    failed = 0
    for name, passed in checks:
        print(("ok    " if passed else "FAIL  ") + name)
        failed += not passed
    if failed:
        print("Some bridge tests failed.")
        sys.exit(1)
    print("All bridge tests passed.")


if __name__ == "__main__":
    main()
