"""Tests for plugins/game-maker-agent/mcp/unreal_bridge.py that need no Unreal Editor.

They check the MCP conversation (initialize, tools/list, errors) with any Python 3,
plus the log reader and the C++ header scan on small examples.
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
    "unreal_read_blueprint",
    "unreal_read_log",
    "unreal_take_screenshot",
    "unreal_run_python",
}


def converse(requests):
    env = dict(os.environ)
    env.pop("GMA_UE_ENGINE_DIR", None)
    lines = "".join(json.dumps(r) + "\n" for r in requests)
    done = subprocess.run([sys.executable, "-I", "-u", BRIDGE], input=lines, capture_output=True, text=True, timeout=60, env=env)
    return {m["id"]: m for m in (json.loads(l) for l in done.stdout.splitlines() if l.strip())}


# A log with engine noise, a repeated warning, a call stack line, and a Play In Editor
# run whose Blueprint compile error is written in the same frame as the PIE start.
LOG = """﻿Log file open, 10/28/26 20:00:00
LogInit: Display: Engine is initialized.
[2026.10.28-20.00.01:000][  1]LogHttp: Warning: request failed, libcurl error: 35
[2026.10.28-20.00.02:000][  2]LogTemp: Warning: Old warning before play
[2026.10.28-20.00.03:000][ 50]LogBlueprint: Error: [Compiler] Variable node Get Score uses an invalid target
[2026.10.28-20.00.03:000][ 50]LogPlayLevel: Creating play world package: /Game/UEDPIE_0_Lvl_Main
[2026.10.28-20.00.04:000][ 60]LogScript: Warning: Accessed None trying to read property Coin
	BP_Coin_C /Game/UEDPIE_0_Lvl_Main.Lvl_Main:PersistentLevel.BP_Coin_C_1
[2026.10.28-20.00.05:000][ 61]LogScript: Warning: Accessed None trying to read property Coin
	BP_Coin_C /Game/UEDPIE_0_Lvl_Main.Lvl_Main:PersistentLevel.BP_Coin_C_1
[2026.10.28-20.00.06:000][ 62]LogTemp: Score is 3
"""

HEADER = """
UCLASS()
class ACoin : public AActor
{
    GENERATED_BODY()
protected:
    UPROPERTY(EditAnywhere, Category="Coin", meta=(ClampMin="0"))
    int32 CoinValue = 1;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Mesh;
    UPROPERTY(EditAnywhere)
    uint8 bSpins : 1;
    UPROPERTY(EditAnywhere)
    float Offsets[3];
    UPROPERTY() TMap<FName, int32> Counts{};
};
"""


def unit_checks():
    sys.path.insert(0, os.path.dirname(BRIDGE))
    import editor_log
    import unreal_bridge
    sys.stdout = unreal_bridge._protocol_out  # the bridge sends prints to stderr; undo that here

    everything = editor_log.report(LOG)
    played = editor_log.report(LOG, since_pie=True, level="all")
    errors = editor_log.report(LOG, level="error")
    noisy = editor_log.report(LOG, include_noise=True)
    return [
        ("log: engine network noise is hidden and counted", "LogHttp: Warning" not in everything and "1 entries from" in everything),
        ("log: include_noise shows it", "libcurl error: 35" in noisy),
        ("log: repeated warnings fold into one with a count", everything.count("Accessed None") == 1 and "(x2)" in everything),
        ("log: call stack lines stay with their entry", "BP_Coin_C_1" in everything),
        ("log: since_play starts with the compile in the PIE start frame", "invalid target" in played and "Old warning" not in played),
        ("log: level all includes plain messages", "Score is 3" in played and "Score is 3" not in everything),
        ("log: level error keeps only errors", "invalid target" in errors and "Accessed None" not in errors),
        ("C++ headers: UPROPERTY names are found", unreal_bridge._uproperty_names(HEADER) == ["CoinValue", "Mesh", "bSpins", "Offsets", "Counts"]),
    ]


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
    ] + unit_checks()
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
