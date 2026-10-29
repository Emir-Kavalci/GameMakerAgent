"""Reads the Unreal Editor's log file (Saved/Logs/<Project>.log) and picks out what an
agent needs: errors and warnings, optionally only since the last Play In Editor run,
with repeats folded together. Standard library only; the editor doesn't have to be
running, so it also shows the last session's log after a crash.
"""

import os
import re

# [2026.10.27-20.18.59:537][  0]LogStreaming: Warning: message
# Lines written before the log timer starts have no timestamp: "LogInit: message".
_ENTRY = re.compile(r"^(?:\[(?P<time>[\d.:-]+)\]\[\s*(?P<frame>\d+)\])?(?P<category>Log\w+|\w+): (?:(?P<severity>Fatal|Error|Warning|Display|Log|Verbose|VeryVerbose): )?(?P<message>.*)$")

# Unreal writes this when Play In Editor (or Simulate) creates the play world. The
# Blueprint compile before it happens in the same frame, so that frame is included.
_PIE_START = re.compile(r"LogPlayLevel: Creating play world package")
# A level load during play (OpenLevel, a restart) writes the same line again, after a
# Browse in the same frame; that is still the same play session.
_TRAVEL = re.compile(r"LogNet: Browse: |UEngine::Browse Started")

SEVERITY_RANK = {"Fatal": 4, "Error": 3, "Warning": 2, "Display": 1, "Log": 1, "Verbose": 0, "VeryVerbose": 0}
_LEVELS = {"error": 3, "warning": 2, "all": 0}

# Engine chatter that is almost never about the game, such as the editor's network
# checks when offline. Hidden unless asked for; the answer says how many were hidden.
NOISY_CATEGORIES = {"LogHttp", "LogDerivedDataCache", "LogEOSSDK"}

MAX_READ_BYTES = 16 * 1024 * 1024  # a long editor session can write hundreds of MB; the end is what matters
MAX_LINE_CHARS = 400


def find_log(project_dir):
    """Path of the editor log for the .uproject in project_dir, or None."""
    try:
        names = sorted(n for n in os.listdir(project_dir) if n.lower().endswith(".uproject"))
    except OSError:
        return None
    for name in names:
        path = os.path.join(project_dir, "Saved", "Logs", os.path.splitext(name)[0] + ".log")
        if os.path.isfile(path):
            return path
    return None


def read_tail(path, max_bytes=MAX_READ_BYTES):
    """The last max_bytes of the file as text, and whether the start was cut off.
    The editor keeps the file open for writing; Windows still allows reading it."""
    size = os.path.getsize(path)
    with open(path, "rb") as handle:
        if size > max_bytes:
            handle.seek(size - max_bytes)
        raw = handle.read()
    text = raw.decode("utf-8-sig", "replace")
    cut = size > max_bytes
    if cut:
        text = text.split("\n", 1)[-1]  # drop the partial first line
    return text, cut


def parse(text):
    """Log entries as dicts (category, severity, message, time, line). Lines without a
    category, such as call stacks, are added to the entry before them."""
    entries = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.rstrip("\r")
        match = _ENTRY.match(line)
        if match:
            entries.append({
                "line": number,
                "time": match.group("time") or "",
                "frame": match.group("frame") or "",
                "category": match.group("category"),
                "severity": match.group("severity") or "Log",
                "message": match.group("message"),
                "pie_start": bool(_PIE_START.search(line)),
                "travel": bool(_TRAVEL.search(line)),
            })
        elif entries and line.strip():
            entries[-1]["message"] += "\n" + line
    return entries


def _is_level_load(entries, index):
    """True when the play world created at entries[index] comes from a level load inside
    a running play session (a Browse in the same frame) rather than a new Play press."""
    frame = entries[index]["frame"]
    i = index - 1
    while frame and i >= 0 and entries[i]["frame"] == frame:
        if entries[i]["travel"]:
            return True
        i -= 1
    return False


def select(entries, level="warning", contains="", category="", since_pie=False, include_noise=True):
    """Filters entries. Returns (entries, note) where note says what since_pie did."""
    note = ""
    if since_pie:
        starts = [i for i, e in enumerate(entries) if e["pie_start"] and not _is_level_load(entries, i)]
        if starts:
            first = starts[-1]
            frame = entries[first]["frame"]
            while frame and first > 0 and entries[first - 1]["frame"] == frame:
                first -= 1
            entries = entries[first:]
            reloads = sum(1 for i, e in enumerate(entries) if e["pie_start"] and _is_level_load(entries, i))
            note = "since the last Play In Editor start (log line {0})".format(entries[0]["line"])
            if reloads:
                note += ", including {0} level load(s) during that play session".format(reloads)
        else:
            note = "no Play In Editor run found in this log, so the whole log"
    minimum = _LEVELS.get((level or "warning").lower(), 2)
    contains = (contains or "").lower()
    category = (category or "").lower()
    picked = []
    for entry in entries:
        if SEVERITY_RANK.get(entry["severity"], 1) < minimum:
            continue
        if category and category not in entry["category"].lower():
            continue
        if not include_noise and not category and entry["category"] in NOISY_CATEGORIES:
            continue
        if contains and contains not in (entry["category"] + " " + entry["message"]).lower():
            continue
        picked.append(entry)
    return picked, note


def fold(entries):
    """Folds entries with the same category, severity and message into one, keeping
    the last occurrence's position and a count."""
    order, by_key = [], {}
    for entry in entries:
        key = (entry["category"], entry["severity"], entry["message"])
        if key in by_key:
            by_key[key]["count"] += 1
            by_key[key]["line"] = entry["line"]
            by_key[key]["time"] = entry["time"]
            order.remove(key)
        else:
            by_key[key] = dict(entry, count=1)
        order.append(key)
    return [by_key[k] for k in order]


def summary(entries):
    """'LogHttp 40, LogBlueprint 2' style counts of errors and warnings by category, most first."""
    counts = {}
    for entry in entries:
        if SEVERITY_RANK.get(entry["severity"], 1) >= 2:
            counts[entry["category"]] = counts.get(entry["category"], 0) + 1
    return ", ".join("{0} {1}".format(c, n) for c, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def format_entry(entry):
    text = entry["message"]
    if len(text) > MAX_LINE_CHARS:
        text = text[:MAX_LINE_CHARS - 3] + "..."
    severity = "" if entry["severity"] == "Log" else entry["severity"] + ": "
    repeat = " (x{0})".format(entry["count"]) if entry.get("count", 1) > 1 else ""
    when = "[{0}] ".format(entry["time"]) if entry["time"] else ""
    return "{0}{1}: {2}{3}{4}".format(when, entry["category"], severity, text, repeat)


def report(text, level="warning", contains="", category="", since_pie=False, limit=100, include_noise=False):
    """The readable answer for unreal_read_log, from the log's text."""
    entries = parse(text)
    picked, note = select(entries, level, contains, category, since_pie, include_noise)
    folded = fold(picked)
    scope = note or "whole log"
    lines = ["{0} matching entries ({1} different), {2}.".format(len(picked), len(folded), scope)]
    counted = summary(select(entries, "warning", "", "", since_pie)[0])
    if counted:
        lines.append("Errors and warnings by category: " + counted)
    if not include_noise and not category:
        hidden = len(select(entries, level, contains, "", since_pie)[0]) - len(picked)
        if hidden:
            lines.append("{0} entries from {1} (engine network and cache messages) hidden; set include_noise to see them.".format(hidden, ", ".join(sorted(NOISY_CATEGORIES))))
    shown = folded[-limit:] if limit > 0 else folded
    if len(folded) > len(shown):
        lines.append("Showing the last {0}; {1} earlier ones not shown (raise limit or filter).".format(len(shown), len(folded) - len(shown)))
    lines += [format_entry(e) for e in shown]
    return "\n".join(lines)
