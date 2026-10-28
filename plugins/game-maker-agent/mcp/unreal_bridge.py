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
import tempfile
import threading

# The bridge runs with python -I, which leaves this folder off the import path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blueprint_text  # noqa: E402
import editor_log  # noqa: E402

SERVER_NAME = "game-maker-agent-unreal"
SERVER_VERSION = "0.5.1"
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

# Reading every property also touches deprecated aliases; keep their warnings out of the user's log.
_PRELUDE = "import unreal, json, warnings\nwarnings.simplefilter('ignore', DeprecationWarning)\ndef _out(data):\n    print('" + _JSON_MARK + "' + json.dumps(data, default=str))\n"


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
    parent_class = args.get("parent_class") or ""
    limit = int(args.get("limit") or 200)
    # Blueprints carry their parent class and nearest C++ ancestor as asset registry tags.
    code = _PRELUDE + (
        "registry = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        "def short(tag):\n"
        "    value = str(tag or '')\n"
        "    if value in ('', 'None'):\n"
        "        return ''\n"
        "    value = value.split(\"'\")[-2] if \"'\" in value else value\n"
        "    value = value.rsplit('.', 1)[-1]\n"
        "    return value[:-2] if value.endswith('_C') else value\n"
        "rows = []\n"
        "for a in registry.get_assets_by_path({path!r}, recursive=True):\n"
        "    cls = str(a.asset_class_path.asset_name)\n"
        "    if '/__External' in str(a.package_name):\n"
        "        continue  # one-file-per-actor level data, not real assets\n"
        "    if {cls!r} and cls.lower() != {cls!r}.lower():\n"
        "        continue\n"
        "    parent = short(a.get_tag_value('ParentClass'))\n"
        "    native = short(a.get_tag_value('NativeParentClass'))\n"
        "    if {parent!r} and {parent!r}.lower() not in (parent.lower(), native.lower()):\n"
        "        continue\n"
        "    rows.append({{'path': str(a.package_name), 'class': cls, 'parent': parent, 'native': native}})\n"
        "rows.sort(key=lambda r: r['path'])\n"
        "_out({{'total': len(rows), 'assets': rows[:{limit}]}})\n"
    ).format(path=path, cls=class_name, parent=parent_class, limit=limit)
    ok, data = _query_editor(code)
    if not ok:
        return False, data
    lines = ["{0} assets under {1}{2}{3}:".format(
        data["total"], path, " of class " + class_name if class_name else "", " based on " + parent_class if parent_class else "")]
    for r in data["assets"]:
        based = ""
        if r.get("parent"):
            based = ", parent " + r["parent"]
            if r.get("native") and r["native"] != r["parent"]:
                based += ", C++ base " + r["native"]
        lines.append("- {0} ({1}{2})".format(r["path"], r["class"], based))
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


def _cpp_property_names(project_dir):
    """Names of the UPROPERTYs declared in the project's C++ headers (Source and project
    plugins). Python lists only the properties Blueprints can see, so protected ones such
    as UPROPERTY(EditAnywhere) members are missing from dir(); they can still be read by name."""
    names = set()
    roots = [os.path.join(project_dir, "Source"), os.path.join(project_dir, "Plugins")]
    for root in roots:
        for folder, _dirs, files in os.walk(root):
            for name in files:
                if not name.endswith(".h"):
                    continue
                try:
                    with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as handle:
                        text = handle.read()
                except OSError:
                    continue
                names.update(_uproperty_names(text))
    return sorted(names)


def _uproperty_names(text):
    found = []
    start = text.find("UPROPERTY")
    while start != -1:
        # skip the balanced (...) after UPROPERTY, then the declaration runs to the next ';'
        i = text.find("(", start)
        depth = 0
        while 0 <= i < len(text):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
            if depth == 0:
                break
        end = text.find(";", i)
        if i < 0 or end < 0:
            break
        declaration = text[i:end].split("=")[0].split("{")[0].split(":")[0].split("[")[0]
        words = [w for w in declaration.replace("*", " ").replace("&", " ").replace(">", " ").split() if w]
        if words and words[-1].isidentifier():
            found.append(words[-1])
        start = text.find("UPROPERTY", end)
    return found


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
        "    own, engine, hidden = {{}}, {{}}, {{}}\n"
        "    def read(name):\n"
        "        value = target.get_editor_property(name)\n"
        "        if callable(value):\n"
        "            raise TypeError(name)\n"
        "        text = re.sub(r' \\(0x[0-9A-Fa-f]+\\)', '', str(value))\n"
        "        return text if len(text) <= 160 else text[:157] + '...'\n"
        "    for name in dir(target):\n"
        "        if name.startswith('_'):\n"
        "            continue\n"
        "        try:\n"
        "            (engine if name in engine_names else own)[name] = read(name)\n"
        "        except Exception:\n"
        "            continue\n"
        "    # C++ UPROPERTYs that Python doesn't list (protected, not visible to Blueprints)\n"
        "    listed = set(n.replace('_', '').lower() for n in dir(target))\n"
        "    for name in {cpp_names!r}:\n"
        "        key = name.lower()\n"
        "        if key in listed or (name[:1] == 'b' and name[1:2].isupper() and key[1:] in listed):\n"
        "            continue\n"
        "        try:\n"
        "            hidden[name] = read(name)\n"
        "        except Exception:\n"
        "            continue\n"
        "    _out({{'kind': kind, 'own': own, 'engine': engine, 'hidden': hidden}})\n"
    ).format(asset=asset, cpp_names=_cpp_property_names(_project_dir()))
    ok, data = _query_editor(code)
    if not ok:
        return False, data
    if "error" in data:
        return False, data["error"]
    lines = ["{0} ({1})".format(asset, data["kind"])]
    lines.append("Project properties ({0}):".format(len(data["own"])))
    lines += ["- {0} = {1}".format(k, v) for k, v in sorted(data["own"].items())] or ["- (none)"]
    if data.get("hidden"):
        lines.append("C++ properties Blueprints can't see (protected or without BlueprintReadOnly/ReadWrite; read and set them by this C++ name) ({0}):".format(len(data["hidden"])))
        lines += ["- {0} = {1}".format(k, v) for k, v in sorted(data["hidden"].items())]
    if include_engine:
        lines.append("Inherited engine properties ({0}):".format(len(data["engine"])))
        lines += ["- {0} = {1}".format(k, v) for k, v in sorted(data["engine"].items())]
    else:
        lines.append("{0} inherited engine properties not shown (set include_engine_properties to see them).".format(len(data["engine"])))
    lines.append("Variables added only in the Blueprint editor aren't listed; unreal_read_blueprint shows them with their defaults.")
    return True, "\n".join(lines)


# The editor exports the Blueprint as T3D text (what copying nodes gives you) into a
# temporary file; blueprint_text turns it into readable steps here, outside the editor.
_READ_BLUEPRINT = (
    "import re\n"
    "bp = unreal.load_asset({asset!r})\n"
    "if not isinstance(bp, unreal.Blueprint):\n"
    "    _out({{'error': 'No Blueprint at ' + {asset!r} + (' (it is a ' + bp.get_class().get_name() + ')' if bp else '')}})\n"
    "else:\n"
    "    task = unreal.AssetExportTask()\n"
    "    task.object = bp\n"
    "    task.exporter = unreal.ObjectExporterT3D()\n"
    "    task.filename = {path!r}\n"
    "    task.automated = True\n"
    "    task.prompt = False\n"
    "    task.replace_identical = True\n"
    "    exported = unreal.Exporter.run_asset_export_task(task)\n"
    "    components = []\n"
    "    try:\n"
    "        lib = unreal.SubobjectDataBlueprintFunctionLibrary\n"
    "        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)\n"
    "        seen = set()\n"
    "        for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):\n"
    "            data = lib.get_data(handle)\n"
    "            name = str(lib.get_variable_name(data))\n"
    "            if not lib.is_component(data) or name in seen:\n"
    "                continue\n"
    "            seen.add(name)\n"
    "            template = lib.get_object_for_blueprint(data, bp) or lib.get_associated_object(data)\n"
    "            parent = lib.get_data(lib.get_parent_handle(data))\n"
    "            components.append({{\n"
    "                'name': name,\n"
    "                'class': template.get_class().get_name() if template else '?',\n"
    "                'parent': str(lib.get_variable_name(parent)) if lib.is_valid(parent) and lib.is_component(parent) else '',\n"
    "                'native': lib.is_native_component(data),\n"
    "                'inherited': lib.is_inherited_component(data),\n"
    "            }})\n"
    "    except Exception:\n"
    "        pass  # not an Actor Blueprint\n"
    "    values = {{}}\n"
    "    try:\n"
    "        text = open({path!r}, 'rb').read().decode('utf-8', 'replace')\n"
    "        cdo = unreal.get_default_object(bp.generated_class())\n"
    "        for name in re.findall(r'NewVariables\\(\\d+\\)=\\(VarName=\"([^\"]+)\"', text):\n"
    "            try:\n"
    "                value = re.sub(r' \\(0x[0-9A-Fa-f]+\\)', '', str(cdo.get_editor_property(name)))\n"
    "                values[name] = value if len(value) <= 160 else value[:157] + '...'\n"
    "            except Exception:\n"
    "                pass\n"
    "    except Exception:\n"
    "        pass\n"
    "    project_file = unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())\n"
    "    try:\n"
    "        modules = [m['Name'] for m in json.load(open(project_file)).get('Modules', [])]\n"
    "    except Exception:\n"
    "        modules = []\n"
    "    modules.append(unreal.SystemLibrary.get_game_name())\n"
    "    _out({{'exported': exported, 'kind': bp.get_class().get_name(), 'components': components, 'values': values, 'modules': modules}})\n"
)


def _read_text_file(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", "replace")


def tool_read_blueprint(args):
    asset = args.get("asset_path") or ""
    if not asset:
        return False, "Give asset_path, for example /Game/Blueprints/BP_Coin (unreal_list_assets with class_name Blueprint lists them)."
    graph = args.get("graph") or ""
    handle, path = tempfile.mkstemp(prefix="gma_blueprint_", suffix=".t3d")
    os.close(handle)
    try:
        ok, data = _query_editor(_PRELUDE + _READ_BLUEPRINT.format(asset=asset, path=path))
        if not ok:
            return False, data
        if "error" in data:
            return False, data["error"]
        if not data.get("exported") or not os.path.getsize(path):
            return False, "The editor could not export " + asset + "."
        reader = blueprint_text.BlueprintReader(_read_text_file(path), data.get("modules") or [], data.get("components"), data.get("values"))
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    text = reader.text(only=graph or None)
    if text is None:
        return False, "No graph named {0} in {1}. Its graphs: {2}".format(graph, asset, ", ".join(reader.graph_names()))
    return True, "{0} ({1})\n{2}".format(asset, data.get("kind", "Blueprint"), text)


def tool_read_log(args):
    # The log is a file in the project, so this works without the editor (and after a crash).
    path = editor_log.find_log(_project_dir())
    if path is None and remote_execution is not None:
        ok, data = _query_editor(_PRELUDE + "_out({'dir': unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_log_dir()), 'name': unreal.SystemLibrary.get_game_name()})\n")
        if ok:
            candidate = os.path.join(data["dir"], data["name"] + ".log")
            path = candidate if os.path.isfile(candidate) else None
    if path is None:
        return False, "No editor log found. It is Saved/Logs/<Project>.log in the project folder and appears after the editor has been opened once."
    text, cut = editor_log.read_tail(path)
    answer = editor_log.report(
        text,
        level=args.get("level") or "warning",
        contains=args.get("contains") or "",
        category=args.get("category") or "",
        since_pie=bool(args.get("since_play")),
        limit=int(args.get("limit") or 100),
        include_noise=bool(args.get("include_noise")),
    )
    header = "Log: " + path + (" (only its last {0} MB read)".format(editor_log.MAX_READ_BYTES // (1024 * 1024)) if cut else "")
    return True, header + "\n" + answer


# In the editor a temporary Scene Capture camera renders the level straight into an
# image: it works while the editor is in the background (its viewport doesn't redraw
# then) and the user's own camera never moves. The camera is a transient actor (never
# saved), removed afterwards, and the user's selection is restored.
# During Play In Editor, Python can't spawn into the play world, so the game's own
# viewport is saved with HighResShot instead; the game keeps drawing while it runs.
_SCREENSHOT = (
    "editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)\n"
    "actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n"
    "game = editor.get_game_world()\n"
    "label = {label!r}\n"
    "if game:\n"
    "    unreal.SystemLibrary.execute_console_command(game, 'HighResShot {width}x{height} filename=\"' + {folder!r}.replace('\\\\', '/') + '/shot.png\"')\n"
    "    _out({{'pie': True}})\n"
    "else:\n"
    "    location, rotation = editor.get_level_viewport_camera_info()\n"
    "    target = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None) if label else None\n"
    "    if label and target is None:\n"
    "        _out({{'error': 'No actor labeled ' + label + ' in the open level'}})\n"
    "    else:\n"
    "        if target is not None:\n"
    "            center, extent = target.get_actor_bounds(False)\n"
    "            rotation = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=rotation.yaw)\n"
    "            location = center - rotation.get_forward_vector() * max(extent.length() * 2.5, 300.0)\n"
    "        world = editor.get_editor_world()\n"
    "        selected = actors.get_selected_level_actors()\n"
    "        capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, location, rotation, transient=True)\n"
    "        try:\n"
    "            component = capture.capture_component2d\n"
    "            image = unreal.RenderingLibrary.create_render_target2d(world, {width}, {height}, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)\n"
    "            component.set_editor_property('texture_target', image)\n"
    "            component.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)\n"
    "            component.set_editor_property('capture_every_frame', False)\n"
    "            component.set_editor_property('capture_on_movement', False)\n"
    "            component.set_editor_property('fov_angle', 90.0)\n"
    "            component.capture_scene()\n"
    "            unreal.RenderingLibrary.export_render_target(world, image, {folder!r}, 'shot.png')\n"
    "        finally:\n"
    "            actors.destroy_actor(capture)\n"
    "            actors.set_selected_level_actors(selected)\n"
    "        _out({{'pie': False}})\n"
)


def _remove_folder(folder):
    for name in os.listdir(folder):
        try:
            os.remove(os.path.join(folder, name))
        except OSError:
            pass
    try:
        os.rmdir(folder)
    except OSError:
        pass


def tool_take_screenshot(args):
    import base64
    import time

    width = max(320, min(int(args.get("width") or 1280), 1920))
    height = max(180, min(int(args.get("height") or 720), 1080))
    label = args.get("actor_label") or ""
    # Images only live in the system temp folder until they are sent. A game screenshot
    # that arrived after an earlier call stopped waiting is removed here.
    temp = tempfile.gettempdir()
    for name in os.listdir(temp):
        stale = os.path.join(temp, name)
        if name.startswith("gma_shot_") and os.path.isdir(stale) and time.time() - os.path.getmtime(stale) > 120:
            _remove_folder(stale)
    folder = tempfile.mkdtemp(prefix="gma_shot_")
    path = os.path.join(folder, "shot.png")
    try:
        ok, data = _query_editor(_PRELUDE + _SCREENSHOT.format(label=label, width=width, height=height, folder=folder))
        if not ok:
            return False, data
        if "error" in data:
            return False, data["error"]
        if data.get("pie"):
            # HighResShot writes on a later frame; wait until the file stops growing.
            deadline, size = time.time() + 30, -1
            while time.time() < deadline:
                time.sleep(0.5)
                if os.path.isfile(path):
                    if os.path.getsize(path) == size > 0:
                        break
                    size = os.path.getsize(path)
            if size <= 0:
                return False, "The game didn't draw a frame within 30 seconds. Is Play In Editor paused or minimized?"
        if not os.path.isfile(path) or not os.path.getsize(path):
            return False, "The editor could not render the screenshot."
        with open(path, "rb") as handle:
            image = base64.b64encode(handle.read()).decode("ascii")
    finally:
        _remove_folder(folder)
    if data.get("pie"):
        what = "the game view (Play In Editor is running), with its on-screen UI" + ("; actor_label is ignored while playing" if label else "")
    elif label:
        what = "the level, looking at {0} (it is in the middle of the picture, possibly hidden by other objects); editor icons are not shown and lighting can look a little darker than in the viewport".format(label)
    else:
        what = "the level from the editor camera; editor icons are not shown and lighting can look a little darker than in the viewport"
    caption = "{0}x{1} picture of {2}.".format(width, height, what)
    return True, [{"type": "text", "text": caption}, {"type": "image", "data": image, "mimeType": "image/png"}]


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
        "description": "List assets in the open project (path and class; for Blueprints also the parent class), from the editor's asset registry. Read-only. Use this instead of guessing from .uasset file names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Content path to search, recursively. Default /Game (the Content folder)."},
                "class_name": {"type": "string", "description": "Only this asset class, for example Blueprint, StaticMesh, Material, World."},
                "parent_class": {"type": "string", "description": "Only Blueprints whose parent class or nearest C++ base class has this name, for example GMATestbedCharacter. Use it to find the Blueprints built on a C++ class before changing that class."},
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
        "description": "Show the editable properties of an asset (for a Blueprint, its class defaults) or of one actor placed in the open level, which can override the defaults. Give either asset_path or actor_label. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_path": {"type": "string", "description": "Asset path, for example /Game/Blueprints/BP_Coin. Shows the Blueprint's class defaults."},
                "actor_label": {"type": "string", "description": "Instead of asset_path: the name of an actor placed in the open level (as unreal_list_level_actors shows it), to see the values set on that one actor."},
                "include_engine_properties": {"type": "boolean", "description": "Also list the properties inherited from engine classes such as Actor. Default false."},
            },
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_get_properties,
    },
    {
        "name": "unreal_read_blueprint",
        "description": (
            "Read a Blueprint's logic as text: parent class (and whether it is this project's C++), components, "
            "variables with defaults, and every graph (Event Graph, functions, Construction Script, Anim Graph) as "
            "indented steps with the values wired into each node. Marks what comes from C++, such as events declared "
            "in C++ and C++ functions it calls. Works for Actor, Widget and Anim Blueprints. Read-only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_path": {"type": "string", "description": "Blueprint asset path, for example /Game/Blueprints/BP_Coin."},
                "graph": {"type": "string", "description": "Only this graph, for example EventGraph or a function name. Use it when the whole Blueprint is too long."},
            },
            "required": ["asset_path"],
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_read_blueprint,
    },
    {
        "name": "unreal_read_log",
        "description": (
            "Read the Unreal Editor's Output Log (Saved/Logs/<Project>.log): errors and warnings by default, repeats "
            "folded, newest last, with counts by category. Use it after a Play In Editor test, a Blueprint compile or a "
            "crash, to see what went wrong; UE_LOG and Print String messages are there too (level all). Works even when "
            "the editor is closed (then it is the last session's log). Read-only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["error", "warning", "all"], "description": "error: errors only. warning (default): errors and warnings. all: every message, including UE_LOG and Print String output."},
                "since_play": {"type": "boolean", "description": "Only messages since the last Play In Editor start. Use it after the user (or you) tested the game."},
                "contains": {"type": "string", "description": "Only messages containing this text (not case-sensitive), for example a class or asset name."},
                "category": {"type": "string", "description": "Only this log category, for example LogBlueprint, LogTemp or LogScript (partial names match)."},
                "limit": {"type": "integer", "description": "Maximum entries to show, newest kept. Default 100."},
                "include_noise": {"type": "boolean", "description": "Also show engine network and cache messages (LogHttp and similar), hidden by default."},
            },
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_read_log,
    },
    {
        "name": "unreal_take_screenshot",
        "description": (
            "Take a picture and return it as an image: the level as seen from the editor camera (without editor icons), "
            "or the game view with its on-screen UI while Play In Editor is running. Use it to see what the level looks "
            "like after a change (placed actors, lighting, materials) or what the player sees. With actor_label the "
            "picture is taken looking at that actor; the user's own camera doesn't move. Works with the editor in the "
            "background. Nothing is saved to the project. Read-only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor_label": {"type": "string", "description": "Take the picture looking at this actor in the open level (as unreal_list_level_actors shows it). Ignored during Play In Editor."},
                "width": {"type": "integer", "description": "Image width in pixels, 320 to 1920. Default 1280."},
                "height": {"type": "integer", "description": "Image height in pixels, 180 to 1080. Default 720."},
            },
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_take_screenshot,
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
        # Handlers return text, or a list of MCP content items (text and images).
        content = text if isinstance(text, list) else [{"type": "text", "text": text}]
        return {"content": content, "isError": not ok}
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
