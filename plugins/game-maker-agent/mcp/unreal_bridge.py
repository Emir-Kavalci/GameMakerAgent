"""GameMakerAgent Unreal bridge: a small MCP server (stdio) that talks to a running
Unreal Editor through Epic's Python remote execution.

It runs with the Python that ships inside Unreal Engine and uses only the standard
library plus Epic's remote_execution.py, which it loads from the engine
installation (it is not copied into this repository).

The editor needs the Python Editor Script Plugin enabled and
Project Settings > Plugins > Python > "Enable Remote Execution?" turned on.
Everything stays on this computer: remote execution only listens on 127.0.0.1.
"""

import json
import os
import sys
import threading

SERVER_NAME = "game-maker-agent-unreal"
SERVER_VERSION = "0.5.0"
SUPPORTED_PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]

# MCP messages go to the real stdout; anything else printed by accident goes to stderr.
_protocol_out = sys.stdout
sys.stdout = sys.stderr

SETUP_HELP = (
    "No Unreal Editor answered. To connect:\n"
    "1. Open your project in the Unreal Editor (and wait until it has fully loaded).\n"
    "2. Edit > Plugins: search for 'Python Editor Script Plugin', tick it, and restart the editor if asked.\n"
    "3. Edit > Project Settings > Plugins > Python: tick 'Enable Remote Execution?'.\n"
    "The /game-maker-agent:gma-init skill can turn on steps 2 and 3 for you while the editor is closed."
)


# ---------------------------------------------------------------------------
# Finding Epic's remote_execution module


def _engine_roots():
    """Engine folders to look in for remote_execution.py, most likely first."""
    roots = []
    # This Python normally is <Engine>/Binaries/ThirdParty/Python3/Win64/python.exe
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    roots.append(os.path.normpath(os.path.join(exe_dir, "..", "..", "..", "..")))
    override = os.environ.get("GMA_UE_ENGINE_DIR")
    if override:
        roots.insert(0, os.path.join(override, "Engine") if not override.rstrip("\\/").endswith("Engine") else override)
    return roots


def _load_remote_execution():
    for root in _engine_roots():
        folder = os.path.join(root, "Plugins", "Experimental", "PythonScriptPlugin", "Content", "Python")
        if os.path.isfile(os.path.join(folder, "remote_execution.py")):
            sys.path.insert(0, folder)
            import remote_execution  # noqa: E402  (Epic's module, from the engine install)
            return remote_execution
    return None


remote_execution = _load_remote_execution()


# ---------------------------------------------------------------------------
# Talking to the editor


def _project_dir():
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _same_folder(a, b):
    return os.path.normcase(os.path.normpath(a or "")) == os.path.normcase(os.path.normpath(b or ""))


_lock = threading.Lock()  # remote execution uses fixed local ports, so one call at a time


def _discover(rex, seconds=3.0):
    """Waits for editors to answer on a started RemoteExecution and returns them,
    as dicts from Epic's 'pong' message (node_id, project_name, project_root, engine_version)."""
    import time

    deadline = time.time() + seconds
    while time.time() < deadline:
        time.sleep(0.25)
        if rex.remote_nodes:
            time.sleep(0.5)  # give other open editors a moment to answer too
            break
    return rex.remote_nodes


def _find_editors():
    rex = remote_execution.RemoteExecution()
    rex.start()
    try:
        return _discover(rex)
    finally:
        rex.stop()


def _in_unreal_project():
    try:
        return any(name.lower().endswith(".uproject") for name in os.listdir(_project_dir()))
    except OSError:
        return False


def _pick_editor(nodes):
    """The editor that has this folder's project open. Outside an Unreal project
    folder, the only editor running. Never a different project's editor when
    Claude Code was started inside an Unreal project."""
    here = _project_dir()
    for node in nodes:
        if _same_folder(node.get("project_root"), here):
            return node
    if len(nodes) == 1 and not _in_unreal_project():
        return nodes[0]
    return None


def _run_in_editor(code, timeout=120):
    """Runs Python code in the matching editor. Returns (ok, text)."""
    if remote_execution is None:
        return False, "Epic's remote_execution.py was not found next to this Python. Set GMA_UE_ENGINE_DIR to your Unreal Engine folder."
    with _lock:
        rex = remote_execution.RemoteExecution()
        rex.start()
        try:
            nodes = _discover(rex)
            if not nodes:
                return False, SETUP_HELP
            node = _pick_editor(nodes)
            if node is None:
                names = ", ".join(n.get("project_name", "?") for n in nodes)
                return False, "The open editor(s) ({0}) don't have the project in {1}. Open this folder's project in the Unreal Editor, or start Claude Code in the folder of the project that is open.".format(names, _project_dir())
            rex.open_command_connection(node["node_id"])
            sock = getattr(rex._command_connection, "_command_channel_socket", None)
            if sock is not None:
                sock.settimeout(timeout)
            result = rex.run_command(code, unattended=True, exec_mode=remote_execution.MODE_EXEC_FILE)
        except Exception as error:  # connection problems, timeouts
            return False, "Lost the connection to the Unreal Editor: {0}".format(error)
        finally:
            try:
                rex.stop()
            except Exception:
                pass
    lines = []
    for entry in result.get("output") or []:
        text = (entry.get("output") or "").rstrip("\n")
        kind = entry.get("type", "Info")
        lines.append(text if kind == "Info" else "[{0}] {1}".format(kind, text))
    if not result.get("success") and result.get("result"):
        lines.append(str(result["result"]))
    return bool(result.get("success")), "\n".join(lines)


_JSON_MARK = "GMA_JSON:"


def _query_editor(code):
    """Runs editor code that prints one line starting with GMA_JSON: and returns (ok, data or error)."""
    ok, text = _run_in_editor(code)
    if ok:
        for line in text.splitlines():
            if line.startswith(_JSON_MARK):
                return True, json.loads(line[len(_JSON_MARK):])
    return False, text


# ---------------------------------------------------------------------------
# Tools. The editor-side code is kept small and read-only except run_python.

_PRELUDE = "import unreal, json\ndef _out(data):\n    print('" + _JSON_MARK + "' + json.dumps(data, default=str))\n"


def tool_status(_args):
    if remote_execution is None:
        return False, "Epic's remote_execution.py was not found. Set GMA_UE_ENGINE_DIR to your Unreal Engine folder."
    with _lock:
        nodes = _find_editors()
    if not nodes:
        return True, SETUP_HELP
    node = _pick_editor(nodes)
    lines = ["Editors found:"]
    for n in nodes:
        mark = " (this project)" if n is node else ""
        lines.append("- {0} at {1}, Unreal Engine {2}{3}".format(n.get("project_name", "?"), n.get("project_root", "?"), n.get("engine_version", "?"), mark))
    if node is None:
        lines.append("None of them has the project in " + _project_dir() + " open.")
    return True, "\n".join(lines)


def tool_list_assets(args):
    path = args.get("path") or "/Game"
    class_name = args.get("class_name") or ""
    limit = int(args.get("limit") or 200)
    code = _PRELUDE + (
        "registry = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        "rows = []\n"
        "for a in registry.get_assets_by_path({path!r}, recursive=True):\n"
        "    cls = str(a.asset_class_path.asset_name)\n"
        "    if '/__External' in str(a.package_name):\n"
        "        continue  # one-file-per-actor level data, not real assets\n"
        "    if {cls!r} and cls.lower() != {cls!r}.lower():\n"
        "        continue\n"
        "    rows.append({{'path': str(a.package_name), 'class': cls}})\n"
        "rows.sort(key=lambda r: r['path'])\n"
        "_out({{'total': len(rows), 'assets': rows[:{limit}]}})\n"
    ).format(path=path, cls=class_name, limit=limit)
    ok, data = _query_editor(code)
    if not ok:
        return False, data
    lines = ["{0} assets under {1}{2}:".format(data["total"], path, " of class " + class_name if class_name else "")]
    lines += ["- {0} ({1})".format(r["path"], r["class"]) for r in data["assets"]]
    if data["total"] > len(data["assets"]):
        lines.append("... {0} more not shown (raise limit or narrow the path).".format(data["total"] - len(data["assets"])))
    return True, "\n".join(lines)


def tool_list_level_actors(args):
    class_name = args.get("class_name") or ""
    limit = int(args.get("limit") or 200)
    code = _PRELUDE + (
        "world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()\n"
        "rows = []\n"
        "for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():\n"
        "    cls = actor.get_class().get_name()\n"
        "    if {cls!r} and {cls!r}.lower() not in cls.lower():\n"
        "        continue\n"
        "    loc = actor.get_actor_location()\n"
        "    rows.append({{'label': actor.get_actor_label(), 'class': cls, 'location': [round(loc.x), round(loc.y), round(loc.z)]}})\n"
        "rows.sort(key=lambda r: r['label'])\n"
        "_out({{'level': world.get_name() if world else '?', 'total': len(rows), 'actors': rows[:{limit}]}})\n"
    ).format(cls=class_name, limit=limit)
    ok, data = _query_editor(code)
    if not ok:
        return False, data
    lines = ["Level {0}: {1} actors{2}:".format(data["level"], data["total"], " matching " + class_name if class_name else "")]
    lines += ["- {0} ({1}) at {2}".format(r["label"], r["class"], r["location"]) for r in data["actors"]]
    if data["total"] > len(data["actors"]):
        lines.append("... {0} more not shown.".format(data["total"] - len(data["actors"])))
    return True, "\n".join(lines)


def tool_get_properties(args):
    asset = args.get("asset_path") or ""
    label = args.get("actor_label") or ""
    if not asset and not label:
        return False, "Give asset_path (for example /Game/Blueprints/BP_Coin) or actor_label (an actor's name in the level, for example BP_Coin2)."
    include_engine = bool(args.get("include_engine_properties"))
    if label:
        find = (
            "obj = None\n"
            "for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():\n"
            "    if actor.get_actor_label() == {label!r}:\n"
            "        obj = actor\n"
            "        break\n"
            "missing = 'No actor labeled ' + {label!r} + ' in the open level'\n"
        ).format(label=label)
        asset = "Level actor " + label
    else:
        find = "obj = unreal.load_asset({asset!r})\nmissing = 'No asset at ' + {asset!r}\n".format(asset=asset)
    # Properties the project's own C++ classes add are listed first; the many
    # properties every Actor inherits from the engine only on request.
    code = _PRELUDE + find + (
        "import re\n"
        "if obj is None:\n"
        "    _out({{'error': missing}})\n"
        "else:\n"
        "    target = obj\n"
        "    kind = obj.get_class().get_name()\n"
        "    if isinstance(obj, unreal.Blueprint):\n"
        "        target = unreal.get_default_object(obj.generated_class())\n"
        "        kind = 'Blueprint class defaults of ' + target.get_class().get_name()\n"
        "    engine_names = set()\n"
        "    for base in type(target).__mro__:\n"
        "        if hasattr(base, 'static_class') and not base.static_class().get_path_name().startswith('/Script/' + unreal.SystemLibrary.get_game_name() + '.'):\n"
        "            engine_names = set(dir(base))\n"
        "            break\n"
        "    own, engine = {{}}, {{}}\n"
        "    for name in dir(target):\n"
        "        if name.startswith('_'):\n"
        "            continue\n"
        "        try:\n"
        "            value = target.get_editor_property(name)\n"
        "        except Exception:\n"
        "            continue\n"
        "        if callable(value):\n"
        "            continue\n"
        "        text = re.sub(r' \\(0x[0-9A-Fa-f]+\\)', '', str(value))\n"
        "        text = text if len(text) <= 160 else text[:157] + '...'\n"
        "        (engine if name in engine_names else own)[name] = text\n"
        "    _out({{'kind': kind, 'own': own, 'engine': engine}})\n"
    ).format(asset=asset)
    ok, data = _query_editor(code)
    if not ok:
        return False, data
    if "error" in data:
        return False, data["error"]
    lines = ["{0} ({1})".format(asset, data["kind"])]
    lines.append("Project properties ({0}):".format(len(data["own"])))
    lines += ["- {0} = {1}".format(k, v) for k, v in sorted(data["own"].items())] or ["- (none)"]
    if include_engine:
        lines.append("Inherited engine properties ({0}):".format(len(data["engine"])))
        lines += ["- {0} = {1}".format(k, v) for k, v in sorted(data["engine"].items())]
    else:
        lines.append("{0} inherited engine properties not shown (set include_engine_properties to see them).".format(len(data["engine"])))
    lines.append("Variables added only in the Blueprint editor aren't listed; read one with unreal_run_python and get_editor_property('<Name>').")
    return True, "\n".join(lines)


def tool_run_python(args):
    code = args.get("code") or ""
    if not code.strip():
        return False, "code is required"
    ok, text = _run_in_editor(code)
    return ok, text or ("Done (no output)." if ok else "The script failed with no output.")


TOOLS = [
    {
        "name": "unreal_status",
        "description": "Check whether an Unreal Editor with this project is open and reachable. Returns setup steps if not. Read-only.",
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True},
        "handler": tool_status,
    },
    {
        "name": "unreal_list_assets",
        "description": "List assets in the open project (path and class), from the editor's asset registry. Read-only. Use this instead of guessing from .uasset file names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Content path to search, recursively. Default /Game (the Content folder)."},
                "class_name": {"type": "string", "description": "Only this asset class, for example Blueprint, StaticMesh, Material, World."},
                "limit": {"type": "integer", "description": "Maximum rows to return. Default 200."},
            },
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_list_assets,
    },
    {
        "name": "unreal_list_level_actors",
        "description": "List the actors in the level currently open in the editor, with class and location. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "class_name": {"type": "string", "description": "Only actors whose class name contains this text."},
                "limit": {"type": "integer", "description": "Maximum rows to return. Default 200."},
            },
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_list_level_actors,
    },
    {
        "name": "unreal_get_properties",
        "description": "Show the editable properties of an asset (for a Blueprint, its class defaults) or of one actor placed in the open level, which can override the defaults. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_path": {"type": "string", "description": "Asset path, for example /Game/Blueprints/BP_Coin. Shows the Blueprint's class defaults."},
                "actor_label": {"type": "string", "description": "Instead of asset_path: the name of an actor placed in the open level (as unreal_list_level_actors shows it), to see the values set on that one actor."},
                "include_engine_properties": {"type": "boolean", "description": "Also list the properties inherited from engine classes such as Actor. Default false."},
            },
            "required": ["asset_path"],
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_get_properties,
    },
    {
        "name": "unreal_run_python",
        "description": (
            "Run a Python script inside the Unreal Editor (the 'unreal' module is available) and return what it prints. "
            "Use it to change assets or the level the safe way, through the editor: set Blueprint defaults, rename assets with "
            "unreal.EditorAssetLibrary, spawn or move actors. The user is asked to approve every script. Prefer small, "
            "focused scripts, print what changed, and save changed assets with unreal.EditorAssetLibrary.save_asset."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to run in the editor."}},
            "required": ["code"],
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True},
        "handler": tool_run_python,
    },
]
_TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


# ---------------------------------------------------------------------------
# MCP over stdio: newline-delimited JSON-RPC 2.0


def _send(message):
    _protocol_out.write(json.dumps(message) + "\n")
    _protocol_out.flush()


def _handle(request):
    method = request.get("method")
    params = request.get("params") or {}
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {
            "protocolVersion": asked if asked in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": "Tools that read and change the open Unreal Editor. Call unreal_status first if a call fails.",
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [{k: v for k, v in t.items() if k != "handler"} for t in TOOLS]}
    if method == "tools/call":
        tool = _TOOLS_BY_NAME.get(params.get("name"))
        if tool is None:
            raise LookupError("Unknown tool: {0}".format(params.get("name")))
        try:
            ok, text = tool["handler"](params.get("arguments") or {})
        except Exception as error:
            ok, text = False, "Bridge error: {0}".format(error)
        return {"content": [{"type": "text", "text": text}], "isError": not ok}
    raise LookupError("Method not found: {0}".format(method))


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError:
            _send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        if "id" not in request:
            continue  # a notification, such as notifications/initialized
        try:
            _send({"jsonrpc": "2.0", "id": request["id"], "result": _handle(request)})
        except LookupError as error:
            _send({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": str(error)}})


if __name__ == "__main__":
    main()
