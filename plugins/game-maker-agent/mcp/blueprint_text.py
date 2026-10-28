"""Turns the text Unreal exports for a Blueprint into a short, readable summary.

The editor exports a Blueprint as T3D text: the same text you get when you copy
nodes in the Blueprint editor. It lists every graph, node, pin and wire. This
module reads that text and writes the logic as indented steps, for example:

    Event BeginPlay
      Set Health = MaxHealth
      Branch(Condition = IsDead)
        True:
          Destroy Actor

Standard library only and no Unreal needed, so it can be tested anywhere.
"""

import re

# ---------------------------------------------------------------------------
# Reading T3D text


def _split_top(text):
    """Splits on commas that are not inside quotes or parentheses."""
    parts, current, depth, quoted, escaped = [], [], 0, False, False
    for ch in text:
        if quoted:
            current.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    if "".join(current).strip():
        parts.append("".join(current))
    return parts


def parse_struct(text):
    """'(A=1,B="x",C=(D=2))' -> {'A': '1', 'B': '"x"', 'C': '(D=2)'}"""
    text = text.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    out = {}
    for part in _split_top(text):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def text_value(value):
    """The plain text of a T3D value: unquotes strings and NSLOCTEXT(...)."""
    value = (value or "").strip()
    if value.startswith("LOCGEN_FORMAT_ORDERED("):
        # A nested category such as "Movement|Jump": a "{0}|{1}" format followed by its parts.
        parts = [text_value(p) for p in re.findall(r'(?:NSLOCTEXT|LOCTEXT|INVTEXT)\((?:[^()"]|"(?:[^"\\]|\\.)*")*\)', value)]
        return "|".join(parts[1:]) if len(parts) > 1 else "".join(parts)
    match = re.match(r"^(?:NSLOCTEXT|LOCTEXT|INVTEXT|LOCGEN_[A-Z]+)\((.*)\)$", value, re.S)
    if match:
        parts = _split_top(match.group(1))
        value = parts[-1].strip() if parts else ""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), value[1:-1])
    return value


def short_name(path):
    """'/Script/CoreUObject.Class'/Script/Engine.Actor'' -> 'Actor', '/Game/A/BP_X.BP_X_C' -> 'BP_X'."""
    path = text_value(path)
    if not path or path == "None":
        return ""
    quoted = re.search(r"'([^']*)'", path)
    if quoted:
        path = quoted.group(1)
    path = path.split(":")[-1]
    path = path.rsplit(".", 1)[-1] if "." in path else path.rsplit("/", 1)[-1]
    return path[:-2] if path.endswith("_C") else path


def _class_path(path):
    """'/Script/CoreUObject.Class'/Script/GMATestbed.CombatCharacter'' -> '/Script/GMATestbed.CombatCharacter'."""
    path = text_value(path)
    quoted = re.search(r"'([^']*)'", path)
    return quoted.group(1) if quoted else path


_BEGIN = re.compile(r'^\s*Begin Object(?: Class=(\S+))? Name="([^"]+)"')


def parse_objects(t3d):
    """Returns the top object of a T3D export as nested dicts:
    {'class', 'name', 'props': {key: raw value}, 'pins': [dict], 'children': [obj]}.
    Unreal writes each object twice (first its class, later its properties); both are merged."""
    stack, objects, top = [], {}, None
    for line in t3d.splitlines():
        begin = _BEGIN.match(line)
        if begin:
            key = tuple(o["name"] for o in stack) + (begin.group(2),)
            obj = objects.get(key)
            if obj is None:
                obj = {"class": "", "name": begin.group(2), "props": {}, "pins": [], "children": []}
                objects[key] = obj
                if stack:
                    stack[-1]["children"].append(obj)
                elif top is None:
                    top = obj
            if begin.group(1):
                obj["class"] = begin.group(1)
            stack.append(obj)
            continue
        stripped = line.strip()
        if stripped == "End Object":
            if stack:
                stack.pop()
            continue
        if not stack:
            continue
        if stripped.startswith("CustomProperties Pin "):
            stack[-1]["pins"].append(parse_struct(stripped[len("CustomProperties Pin "):]))
        elif "=" in stripped and not stripped.startswith("CustomProperties"):
            key, value = stripped.split("=", 1)
            stack[-1]["props"][key] = value
    return top


def prop_list(obj, name):
    """Values of an array property such as UbergraphPages(0), UbergraphPages(1), in order."""
    rows = []
    for key, value in obj["props"].items():
        match = re.match(re.escape(name) + r"\((\d+)\)$", key)
        if match:
            rows.append((int(match.group(1)), value))
    return [value for _, value in sorted(rows)]


def _class_short(obj):
    return obj["class"].rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# Types and values

_BASIC_TYPES = {
    "bool": "Boolean", "byte": "Byte", "int": "Integer", "int64": "Integer64", "real": "Float",
    "float": "Float", "double": "Float", "name": "Name", "string": "String", "text": "Text",
    "exec": "Exec", "wildcard": "Wildcard", "delegate": "Event", "mcdelegate": "Event Dispatcher",
}


def type_name(fields):
    """A readable type from pin type fields (PinCategory, PinSubCategoryObject, ContainerType)."""
    category = text_value(fields.get("PinCategory") or fields.get("PinType.PinCategory") or "")
    sub_object = short_name(fields.get("PinSubCategoryObject") or fields.get("PinType.PinSubCategoryObject") or "")
    container = text_value(fields.get("ContainerType") or fields.get("PinType.ContainerType") or "")
    if category in ("object", "interface", "struct", "enum") or (category == "byte" and sub_object):
        base = sub_object or category
    elif category == "class":
        base = (sub_object or "Object") + " class"
    elif category == "softobject":
        base = (sub_object or "Object") + " (soft reference)"
    elif category == "softclass":
        base = (sub_object or "Object") + " class (soft reference)"
    else:
        base = _BASIC_TYPES.get(category, category or "?")
    if container in ("Array", "Set"):
        return "{0} of {1}".format(container, base)
    if container == "Map":
        return "Map of {0} to ...".format(base)
    return base


def origin(class_path, project_modules):
    """Where a class comes from: this project's C++, a Blueprint, or the engine."""
    path = _class_path(class_path)
    if path.startswith("/Script/"):
        module = path[len("/Script/"):].split(".", 1)[0]
        return "C++ in this project" if module in project_modules else "engine C++"
    if path.startswith("/Game/"):
        return "Blueprint in this project"
    return "plugin or engine content"


# ---------------------------------------------------------------------------
# Graph model


class _Pin(object):
    def __init__(self, node, fields):
        self.node = node
        self.fields = fields
        self.id = fields.get("PinId", "")
        self.name = text_value(fields.get("PinName", ""))
        raw_friendly = fields.get("PinFriendlyName", "")
        if raw_friendly.startswith("LOCGEN_FORMAT"):
            # A split struct pin, such as "New Location X".
            friendly = " ".join(re.findall(r'INVTEXT\("([^"]*)"\)', raw_friendly))
        else:
            friendly = text_value(raw_friendly)
        self.label = friendly if friendly.strip() else self.name
        self.output = fields.get("Direction", "") == '"EGPD_Output"'
        self.category = text_value(fields.get("PinType.PinCategory", ""))
        self.hidden = fields.get("bHidden") == "True" or fields.get("bOrphanedPin") == "True"
        self.advanced = fields.get("bAdvancedView") == "True"
        self.links = []
        linked = fields.get("LinkedTo", "")
        if linked:
            for part in _split_top(linked.strip()[1:-1]):
                bits = part.split()
                if len(bits) == 2:
                    self.links.append((bits[0], bits[1]))

    @property
    def is_exec(self):
        return self.category == "exec"

    def literal(self):
        for key in ("DefaultTextValue", "DefaultObject", "DefaultValue"):
            raw = self.fields.get(key)
            if raw is None or raw == "None" or raw == '""':
                continue
            value = short_name(raw) if key == "DefaultObject" else text_value(raw)
            if value == "":
                continue
            if self.category in ("string", "text"):
                return '"{0}"'.format(value)
            return _tidy_numbers(value)
        auto = text_value(self.fields.get("AutogeneratedDefaultValue", ""))
        if auto:
            return _tidy_numbers(auto)
        # Unreal leaves the value out when it is the type's zero value.
        if self.category == "struct":
            struct = short_name(self.fields.get("PinType.PinSubCategoryObject", ""))
            return {"Vector": "0,0,0", "Rotator": "0,0,0", "Vector2D": "0,0"}.get(struct)
        return {"int": "0", "int64": "0", "byte": "0", "real": "0.0", "float": "0.0", "double": "0.0", "bool": "false"}.get(self.category)

    def default_is_untouched(self):
        """True when the pin still has the value the function declares as its default."""
        auto = self.fields.get("AutogeneratedDefaultValue")
        if auto is None or "DefaultObject" in self.fields or "DefaultTextValue" in self.fields:
            return False
        return text_value(auto) == text_value(self.fields.get("DefaultValue", ""))


def _tidy_numbers(text):
    """'500.000000' -> '500.0', '0.250000' -> '0.25'."""
    return re.sub(r"\b(\d+)\.(\d*?)0+\b", lambda m: "{0}.{1}".format(m.group(1), m.group(2) or "0"), text)


class _Node(object):
    def __init__(self, obj):
        self.obj = obj
        self.name = obj["name"]
        self.kind = _class_short(obj)
        self.props = obj["props"]
        self.pins = [_Pin(self, fields) for fields in obj["pins"]]
        self.x = int(self.props.get("NodePosX", "0") or 0)
        self.y = int(self.props.get("NodePosY", "0") or 0)

    def prop(self, key):
        return text_value(self.props.get(key, ""))

    def member(self, key):
        return parse_struct(self.props.get(key, "()"))

    def visible(self, output, exec_pins):
        return [p for p in self.pins if p.output == output and p.is_exec == exec_pins and not p.hidden]

    @property
    def has_exec(self):
        return any(p.is_exec for p in self.pins if not p.hidden)

    @property
    def disabled(self):
        return self.props.get("EnabledState") in ("Disabled", "DevelopmentOnly")


_ENTRY_KINDS = {
    "K2Node_Event", "K2Node_CustomEvent", "K2Node_ComponentBoundEvent", "K2Node_ActorBoundEvent",
    "K2Node_EnhancedInputAction", "K2Node_InputAction", "K2Node_InputKey", "K2Node_InputAxisEvent",
    "K2Node_InputAxisKeyEvent", "K2Node_InputTouch", "K2Node_FunctionEntry",
}

_OPERATORS = {
    "Add": "+", "Subtract": "-", "Multiply": "*", "Divide": "/", "Percent": "%", "Greater": ">",
    "Less": "<", "GreaterEqual": ">=", "LessEqual": "<=", "EqualEqual": "==", "NotEqual": "!=",
    "BooleanAND": "AND", "BooleanOR": "OR", "BooleanXOR": "XOR",
}

_EVENT_NAMES = {
    "ReceiveBeginPlay": "BeginPlay", "ReceiveTick": "Tick", "ReceiveEndPlay": "EndPlay",
    "ReceiveDestroyed": "Destroyed", "ReceiveHit": "Hit", "ReceiveAnyDamage": "AnyDamage",
    "ReceiveActorBeginOverlap": "ActorBeginOverlap", "ReceiveActorEndOverlap": "ActorEndOverlap",
    "BlueprintUpdateAnimation": "Blueprint Update Animation",
    "BlueprintInitializeAnimation": "Blueprint Initialize Animation",
}


def _function_label(name):
    for prefix in ("K2_", "BP_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name


def _words(class_short):
    """K2Node_GetArrayItem -> 'Get Array Item'."""
    name = re.sub(r"^(K2Node_|AnimGraphNode_|EdGraphNode_)", "", class_short)
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)


class _Graph(object):
    def __init__(self, obj, reader):
        self.obj = obj
        self.name = obj["name"]
        self.reader = reader
        self.nodes = {}
        self.comments = []
        for child in obj["children"]:
            node = _Node(child)
            if node.kind == "EdGraphNode_Comment":
                text = node.prop("NodeComment").strip()
                if text:
                    width = int(node.props.get("NodeWidth", "0") or 0)
                    height = int(node.props.get("NodeHeight", "0") or 0)
                    self.comments.append((node.x, node.y, node.x + width, node.y + height, text))
            else:
                self.nodes[node.name] = node
        self.pin_by_id = {}
        for node in self.nodes.values():
            for pin in node.pins:
                self.pin_by_id[(node.name, pin.id)] = pin

    # -- following wires

    def linked(self, pin):
        """Pins at the other end of a wire, with reroute (Knot) nodes skipped."""
        found = []
        for node_name, pin_id in pin.links:
            other = self.pin_by_id.get((node_name, pin_id))
            if other is None:
                continue
            if other.node.kind == "K2Node_Knot":
                through = [p for p in other.node.pins if p.output != other.output]
                for p in through:
                    found += self.linked(p)
            else:
                found.append(other)
        return found

    def comment_for(self, node):
        best = None
        for left, top, right, bottom, text in self.comments:
            if left <= node.x <= right and top <= node.y <= bottom:
                area = (right - left) * (bottom - top)
                if best is None or area < best[0]:
                    best = (area, text)
        return best[1] if best else None

    # -- names

    def title(self, node):
        kind = node.kind
        r = self.reader
        if kind == "K2Node_Event":
            ref = node.member("EventReference")
            member = text_value(ref.get("MemberName", ""))
            label = "Event " + _EVENT_NAMES.get(member, member)
            if r.origin_of(ref.get("MemberParent", "")) == "C++ in this project":
                label += " [event declared in C++]"
            return label
        if kind == "K2Node_CustomEvent":
            return "Custom Event " + node.prop("CustomFunctionName")
        if kind == "K2Node_ComponentBoundEvent":
            return "On {0} ({1})".format(node.prop("DelegatePropertyName"), node.prop("ComponentPropertyName"))
        if kind == "K2Node_ActorBoundEvent":
            return "On " + node.prop("DelegatePropertyName")
        if kind == "K2Node_EnhancedInputAction":
            return "Input Action " + short_name(node.props.get("InputAction", ""))
        if kind in ("K2Node_InputAction", "K2Node_InputAxisEvent"):
            return "Input " + (node.prop("InputActionName") or node.prop("InputAxisName"))
        if kind == "K2Node_InputKey":
            return "Key " + (text_value(node.member("InputKey").get("KeyName", "")) or node.prop("InputKey"))
        if kind == "K2Node_FunctionEntry":
            return "Start of " + self.name
        if kind == "K2Node_FunctionResult":
            return "Return"
        if kind in ("K2Node_CallFunction", "K2Node_CallArrayFunction", "K2Node_CallMaterialParameterCollectionFunction",
                    "K2Node_CallParentFunction", "K2Node_Message", "K2Node_AddComponent", "K2Node_AddComponentByClass",
                    "K2Node_CommutativeAssociativeBinaryOperator", "K2Node_PromotableOperator"):
            ref = node.member("FunctionReference")
            label = _function_label(text_value(ref.get("MemberName", "")))
            parent = ref.get("MemberParent", "")
            if kind == "K2Node_CallParentFunction":
                label = "Parent: " + _EVENT_NAMES.get(text_value(ref.get("MemberName", "")), label)
            elif kind == "K2Node_Message":
                return "{0} [interface {1}]".format(label, short_name(parent))
            elif kind == "K2Node_AddComponent":
                label = "Add Component " + short_name(node.props.get("TemplateType", ""))
            if parent and kind != "K2Node_CallParentFunction":
                where = r.origin_of(parent)
                owner = short_name(parent)
                if where == "C++ in this project":
                    label = "{0}.{1} [C++]".format(owner, label)
                elif where == "Blueprint in this project":
                    label = "{0}.{1} [Blueprint]".format(owner, label)
            elif (ref.get("bSelfContext") == "True" and kind == "K2Node_CallFunction"
                  and not any(p.name == "self" and p.links for p in node.pins)):
                member = text_value(ref.get("MemberName", ""))
                if member in r.function_names:
                    label += " [function in this Blueprint]"
                elif member in r.custom_events:
                    label += " [custom event in this Blueprint]"
                else:
                    label += " [inherited from parent class]"
            return label
        if kind in ("K2Node_VariableGet", "K2Node_VariableSet"):
            name = text_value(node.member("VariableReference").get("MemberName", ""))
            return ("Set " if kind == "K2Node_VariableSet" else "") + name
        if kind == "K2Node_DynamicCast":
            return "Cast to " + short_name(node.props.get("TargetType", ""))
        if kind == "K2Node_IfThenElse":
            return "Branch"
        if kind == "K2Node_ExecutionSequence":
            return "Sequence"
        if kind == "K2Node_MacroInstance":
            macro = parse_struct(node.props.get("MacroGraphReference", "()")).get("MacroGraph", "")
            return short_name(macro) or "Macro"
        if kind == "K2Node_Timeline":
            return "Timeline " + node.prop("TimelineName")
        if kind == "K2Node_Self":
            return "self"
        if kind in ("K2Node_MakeStruct", "K2Node_BreakStruct", "K2Node_SetFieldsInStruct"):
            verb = {"K2Node_MakeStruct": "Make", "K2Node_BreakStruct": "Break", "K2Node_SetFieldsInStruct": "Set fields in"}[kind]
            return "{0} {1}".format(verb, short_name(node.props.get("StructType", "")))
        if kind in ("K2Node_CallDelegate", "K2Node_AddDelegate", "K2Node_AssignDelegate", "K2Node_RemoveDelegate", "K2Node_ClearDelegate"):
            verb = {"K2Node_CallDelegate": "Call", "K2Node_AddDelegate": "Bind to", "K2Node_AssignDelegate": "Bind to",
                    "K2Node_RemoveDelegate": "Unbind from", "K2Node_ClearDelegate": "Unbind all from"}[kind]
            return "{0} {1}".format(verb, text_value(node.member("DelegateReference").get("MemberName", "")))
        if kind == "K2Node_CreateDelegate":
            return "Event " + node.prop("SelectedFunctionName")
        if kind == "K2Node_SpawnActorFromClass":
            return "Spawn Actor"
        if kind == "K2Node_Composite":
            return "Collapsed graph " + short_name(node.props.get("BoundGraph", ""))
        if kind == "K2Node_GetSubsystem":
            return "Get " + short_name(node.props.get("CustomClass", ""))
        if kind == "K2Node_MathExpression":
            return "Math: " + node.prop("Expression")
        if kind.startswith("K2Node_Switch"):
            return "Switch on " + (short_name(node.props.get("Enum", "")) or _words(kind)[len("Switch "):])
        if kind == "AnimGraphNode_StateMachine":
            return "State Machine " + short_name(node.props.get("EditorStateMachineGraph", ""))
        if kind in ("AnimGraphNode_SequencePlayer", "AnimGraphNode_BlendSpacePlayer"):
            asset = re.search(r"(?:Sequence|BlendSpace)=(\"[^\"]*\"|[^,)]+)", node.props.get("Node", ""))
            return "{0} {1}".format(_words(kind), short_name(asset.group(1)) if asset else "").strip()
        if kind == "AnimGraphNode_SaveCachedPose":
            return "Save cached pose " + node.prop("CacheName")
        return _words(kind)

    # -- values

    def value_of(self, pin, depth):
        """A readable expression for what flows into an input pin."""
        sources = self.linked(pin)
        if sources:
            return self.output_text(sources[0], depth)
        return pin.literal()

    def output_text(self, pin, depth):
        node = pin.node
        kind = node.kind
        if kind == "K2Node_VariableSet":
            return self.title(node)[len("Set "):]
        if kind == "K2Node_VariableGet":
            target = [p for p in node.visible(False, False) if p.name == "self" and p.links]
            name = self.title(node)
            return "{0}.{1}".format(self.value_of(target[0], depth + 1), name) if target else name
        if kind == "K2Node_Self":
            return "self"
        if kind in _ENTRY_KINDS or kind == "K2Node_Tunnel":
            return pin.label
        if kind == "K2Node_BreakStruct":
            inputs = node.visible(False, False)
            source = self.value_of(inputs[0], depth + 1) if inputs else "?"
            return "{0}.{1}".format(source, pin.label)
        if node.has_exec:
            return "[{0}].{1}".format(self.title(node), pin.label)
        if depth > 4:
            return "..."
        inputs = [p for p in node.visible(False, False) if not (p.name == "self" and not p.links)]
        operator = self._operator(node)
        tolerance = [p for p in inputs if "Tolerance" in p.name]
        operands = [p for p in inputs if p not in tolerance]
        if operator and len(operands) >= 2:
            parts = [self._wrap(self.value_of(p, depth + 1)) for p in operands]
            text = (" " + operator + " ").join(parts)
            if tolerance:
                text += " (tolerance {0})".format(self.value_of(tolerance[0], depth + 1))
            return text
        if operator == "NOT" and inputs:
            return "NOT " + self._wrap(self.value_of(inputs[0], depth + 1))
        text = "{0}({1})".format(self.title(node), self.args(inputs, depth + 1, named=len(inputs) > 1, hide_defaults=False))
        outputs = node.visible(True, False)
        if len(outputs) > 1 and pin.name != "ReturnValue":
            text += "." + pin.label
        return text

    @staticmethod
    def _wrap(text):
        """Parentheses around a sub-expression that has an operator, so 'a + b * c' stays clear."""
        text = text or "?"
        if re.search(r" (?:[-+*/%<>]|[<>=!]=|AND|OR|XOR) ", text) or text.startswith("NOT "):
            return "({0})".format(text)
        return text

    def _operator(self, node):
        if node.kind == "K2Node_PromotableOperator":
            return _OPERATORS.get(node.prop("OperationName"))
        if node.kind not in ("K2Node_CommutativeAssociativeBinaryOperator", "K2Node_CallFunction"):
            return None
        ref = node.member("FunctionReference")
        if "KismetMathLibrary" not in ref.get("MemberParent", ""):
            return None
        name = text_value(ref.get("MemberName", ""))
        if name.startswith("Not_"):
            return "NOT"
        return _OPERATORS.get(name.split("_", 1)[0])

    def args(self, pins, depth, named=True, hide_defaults=True):
        """Inputs as 'Name = value'. Steps leave out inputs still at the function's default
        (such as bSweep = false); calculations keep them, because there they are the logic."""
        parts = []
        for pin in pins:
            if pin.name == "self" and not pin.links:
                continue
            if hide_defaults and not pin.links and pin.default_is_untouched():
                continue
            value = self.value_of(pin, depth)
            if value is None:
                continue
            parts.append("{0} = {1}".format(pin.label, value) if named else value)
        return ", ".join(parts)

    # -- steps

    def statement(self, node):
        data_in = node.visible(False, False)
        if node.kind == "K2Node_VariableSet":
            value_pins = [p for p in data_in if p.name != "self"]
            value = self.value_of(value_pins[0], 0) if value_pins else None
            text = "{0} = {1}".format(self.title(node), value if value is not None else "(default)")
        elif node.kind == "K2Node_VariableGet":
            text = "Check that {0} is valid".format(self.title(node))
        elif node.kind == "K2Node_FunctionResult":
            text = "Return" + (" (" + self.args(data_in, 0) + ")" if self.args(data_in, 0) else "")
        elif node.kind == "K2Node_SpawnActorFromClass":
            cls = [p for p in data_in if p.name == "Class"]
            rest = [p for p in data_in if p.name != "Class"]
            text = "Spawn Actor {0}({1})".format((self.value_of(cls[0], 0) or "?") if cls else "?", self.args(rest, 0))
        else:
            arguments = self.args(data_in, 0)
            text = self.title(node) + ("(" + arguments + ")" if arguments else "")
        if node.disabled:
            text += "  [disabled]"
        return text

    def entries(self):
        found = []
        for node in self.nodes.values():
            exec_out = node.visible(True, True)
            exec_in = node.visible(False, True)
            if not exec_out or any(self.linked(p) for p in exec_in):
                continue
            if node.kind in _ENTRY_KINDS or node.kind == "K2Node_Tunnel" or not exec_in:
                found.append(node)
        found.sort(key=lambda n: (n.kind != "K2Node_FunctionEntry", n.y, n.x))
        return found

    def walk(self, node, indent, seen, lines, state):
        while node is not None:
            if node.name in seen:
                lines.append(indent + "(continues at {0}, shown above)".format(self.title(node)))
                return
            seen.add(node.name)
            comment = self.comment_for(node)
            if comment and comment != state.get("comment"):
                lines.append(indent + "// " + " ".join(comment.split()))
            state["comment"] = comment
            lines.append(indent + self.statement(node))
            outs = node.visible(True, True)
            wired = [(p, self.linked(p)) for p in outs]
            wired = [(p, t) for p, t in wired if t]
            if not wired:
                return
            if len(outs) == 1:
                node = wired[0][1][0].node
                continue
            for pin, targets in wired:
                lines.append(indent + "  " + (pin.label or pin.name) + ":")
                self.walk(targets[0].node, indent + "    ", seen, lines, state)
            return

    def render(self, heading):
        lines = []
        entries = self.entries()
        seen = set()
        for entry in entries:
            outs = entry.visible(True, True)
            if not any(self.linked(p) for p in outs) and entry.kind != "K2Node_FunctionEntry":
                continue  # an event placed in the graph but not used
            params = [p for p in entry.visible(True, False) if p.name != "OutputDelegate"]
            label = self.title(entry) if entry.kind != "K2Node_FunctionEntry" else heading
            if params:
                label += " (" + ", ".join("{0}: {1}".format(p.label, type_name(p.fields)) for p in params) + ")"
            if entry.kind == "K2Node_FunctionEntry":
                local = [parse_struct(v) for v in prop_list(entry.obj, "LocalVariables")]
                if local:
                    label += "\n  Local variables: " + ", ".join(
                        "{0} ({1})".format(text_value(v.get("VarName", "")), type_name(parse_struct(v.get("VarType", "()")))) for v in local)
            state = {"comment": None}
            comment = self.comment_for(entry)
            if comment:
                lines.append("// " + " ".join(comment.split()))
                state["comment"] = comment
            lines.append(label)
            seen.add(entry.name)
            if len(outs) == 1:
                targets = self.linked(outs[0])
                if targets:
                    self.walk(targets[0].node, "  ", seen, lines, state)
                elif entry.kind == "K2Node_FunctionEntry":
                    lines.append("  (no steps)")
            else:
                for pin in outs:
                    targets = self.linked(pin)
                    if targets:
                        lines.append("  " + pin.label + ":")
                        self.walk(targets[0].node, "    ", seen, lines, state)
            lines.append("")
        # Anim graphs and other graphs without exec wires: show what feeds the output pose.
        if not entries:
            roots = [n for n in self.nodes.values() if n.kind in ("AnimGraphNode_Root", "AnimGraphNode_StateResult", "AnimGraphNode_TransitionResult")]
            for root in roots:
                inputs = root.visible(False, False)
                parts = [self.value_of(p, 0) for p in inputs if self.linked(p)]
                lines.append("Output pose = " + (", ".join(parts) if parts else "(nothing connected)"))
        unreached = [n for n in self.nodes.values() if n.has_exec and n.name not in seen and n.kind not in _ENTRY_KINDS
                     and n.kind not in ("K2Node_Knot", "K2Node_Tunnel")]
        if unreached:
            lines.append("Not connected to any event: " + ", ".join(sorted({self.title(n) for n in unreached})))
        while lines and lines[-1] == "":
            lines.pop()
        return lines


# ---------------------------------------------------------------------------
# The whole Blueprint


_FLAG_EDIT = 0x1
_FLAG_NET = 0x20
_FLAG_DISABLE_EDIT_ON_INSTANCE = 0x10000
_FLAG_EXPOSE_ON_SPAWN = 0x0001000000000000


class BlueprintReader(object):
    def __init__(self, t3d, project_modules=(), components=None, variable_values=None):
        self.top = parse_objects(t3d)
        if self.top is None:
            raise ValueError("The export has no Blueprint in it.")
        self.project_modules = set(project_modules)
        self.components = components or []
        self.variable_values = variable_values or {}
        self.children = {c["name"]: c for c in self.top["children"]}
        self.function_names = {short_name(v) for v in prop_list(self.top, "FunctionGraphs")}
        self.custom_events = set()
        for value in prop_list(self.top, "UbergraphPages"):
            for node in self.children.get(short_name(value), {"children": []})["children"]:
                if node["class"].endswith(".K2Node_CustomEvent"):
                    self.custom_events.add(text_value(node["props"].get("CustomFunctionName", "")))

    def origin_of(self, class_path):
        return origin(class_path, self.project_modules)

    def _graphs(self):
        """(heading, graph name) for every graph the user can open in the Blueprint editor."""
        found = []
        for value in prop_list(self.top, "UbergraphPages"):
            found.append(("Event Graph", short_name(value)))
        for value in prop_list(self.top, "FunctionGraphs"):
            name = short_name(value)
            if name == "UserConstructionScript":
                found.append(("Construction Script", name))
            elif "AnimationGraph" in value:
                found.append(("Anim Graph", name))
            else:
                found.append(("Function " + name, name))
        for value in prop_list(self.top, "MacroGraphs"):
            found.append(("Macro " + short_name(value), short_name(value)))
        for value in prop_list(self.top, "ImplementedInterfaces"):
            for graph in re.findall(r"EdGraph'([^']+)'", value):
                found.append(("Interface function " + graph, graph))
        return found

    def graph_names(self):
        return [name for _, name in self._graphs()]

    def summary_lines(self):
        top = self.top
        lines = []
        parent = top["props"].get("ParentClass", "")
        if parent:
            lines.append("Parent class: {0} ({1}: {2})".format(short_name(parent), self.origin_of(parent), _class_path(parent)))
        interfaces = [short_name(parse_struct(v).get("Interface", "")) for v in prop_list(top, "ImplementedInterfaces")]
        if interfaces:
            lines.append("Interfaces: " + ", ".join(interfaces))

        if self.components:
            lines.append("")
            lines.append("Components:")
            by_parent = {}
            for comp in self.components:
                by_parent.setdefault(comp.get("parent") or "", []).append(comp)

            def add(parent_name, depth):
                for comp in by_parent.get(parent_name, []):
                    mark = " [from C++ parent class]" if comp.get("native") else (" [from parent Blueprint]" if comp.get("inherited") else "")
                    lines.append("{0}- {1} ({2}){3}".format("  " * depth, comp["name"], comp["class"], mark))
                    if comp["name"] != parent_name:
                        add(comp["name"], depth + 1)

            add("", 1)

        variables = [parse_struct(v) for v in prop_list(top, "NewVariables")]
        if variables:
            lines.append("")
            lines.append("Variables added in this Blueprint:")
            for var in variables:
                name = text_value(var.get("VarName", ""))
                var_type = type_name(parse_struct(var.get("VarType", "()")))
                notes = []
                try:
                    flags = int(var.get("PropertyFlags", "0"))
                except ValueError:
                    flags = 0
                if flags & _FLAG_EDIT and not flags & _FLAG_DISABLE_EDIT_ON_INSTANCE:
                    notes.append("instance editable")
                if flags & _FLAG_EXPOSE_ON_SPAWN:
                    notes.append("expose on spawn")
                if flags & _FLAG_NET:
                    notes.append("replicated")
                category = text_value(var.get("Category", ""))
                if category and category != "Default":
                    notes.append("category " + category)
                value = self.variable_values.get(name)
                if value is None and var.get("DefaultValue"):
                    value = text_value(var["DefaultValue"])
                if value:
                    # The editor prints structs as <Struct 'Vector' {x: 0.000000, ...}>.
                    value = _tidy_numbers(re.sub(r"^<Struct '[^']*' \{(.*)\}>$", r"(\1)", value))
                text = "- {0}: {1}".format(name, var_type)
                if value not in (None, ""):
                    text += " = " + value
                if notes:
                    text += " (" + ", ".join(notes) + ")"
                lines.append(text)

        widgets = [text_value(parse_struct(v).get("VarName", "")) for v in prop_list(top, "GeneratedVariables")]
        if widgets:
            lines.append("")
            lines.append("Widgets usable as variables: " + ", ".join(widgets))
        dispatchers = [short_name(v) for v in prop_list(top, "DelegateSignatureGraphs")]
        if dispatchers:
            lines.append("Event dispatchers: " + ", ".join(d.replace("__DelegateSignature", "") for d in dispatchers))
        timelines = [short_name(v).replace("_Template", "") for v in prop_list(top, "Timelines")]
        if timelines:
            lines.append("Timelines: " + ", ".join(timelines))
        return lines

    def graph_sections(self, only=None):
        """[(graph name, lines)] for each graph, or only the one named."""
        sections = []
        for heading, name in self._graphs():
            if only and name.lower() != only.lower():
                continue
            obj = self.children.get(name)
            if obj is None:
                continue
            plain = name in heading or name in ("EventGraph", "UserConstructionScript", "AnimGraph")
            lines = ["", "== {0} ==".format(heading if plain else "{0} ({1})".format(heading, name))]
            lines += _Graph(obj, self).render(heading) or ["(empty)"]
            sections.append((name, lines))
        return sections

    def text(self, only=None, max_lines=400):
        """The readable summary, or None when the graph asked for doesn't exist. A Blueprint
        too long to show whole gets its overview and a list of graphs to read one by one."""
        sections = self.graph_sections(only)
        if only and not sections:
            return None
        lines = [] if only else self.summary_lines()
        total = len(lines) + sum(len(body) for _, body in sections)
        if total > max_lines and not only and len(sections) > 1:
            lines += ["", "This Blueprint is long. Read one graph at a time with the graph argument:"]
            lines += ["- {0} ({1} lines)".format(name, len(body) - 2) for name, body in sections]
            return "\n".join(lines).strip("\n")
        for _, body in sections:
            lines += body
        if len(lines) > max_lines:
            hidden = len(lines) - max_lines
            lines = lines[:max_lines] + ["... {0} more lines not shown.".format(hidden)]
        return "\n".join(lines).strip("\n")
