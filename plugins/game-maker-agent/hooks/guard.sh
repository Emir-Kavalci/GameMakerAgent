#!/usr/bin/env bash
# GameMakerAgent safety guard (PreToolUse hook).
# Only acts inside an Unreal project (a folder with a .uproject file):
# - denies Write/Edit on .uasset/.umap files (binary assets; use the editor)
# - denies Write/Edit inside an Unreal Engine installation
# - asks the user before shell commands that delete or discard files
# Reads the hook input JSON on stdin. Uses only grep, so it needs no jq.

input=$(tr -d '\r\n')

project_dir="${CLAUDE_PROJECT_DIR:-$PWD}"
if ! ls "$project_dir"/*.uproject >/dev/null 2>&1; then
  exit 0
fi

# A JSON string literal: quotes around any mix of non-quote/non-backslash
# characters and backslash escapes.
json_string='"([^"\\]|\\.)*"'

# Prints the raw (still escaped) value of the first JSON field with this name.
field() {
  printf '%s' "$input" | grep -oE "\"$1\"[[:space:]]*:[[:space:]]*$json_string" | head -n 1 \
    | sed -E "s/^\"$1\"[[:space:]]*:[[:space:]]*\"//; s/\"\$//"
}

decide() {
  # $1 = deny | ask, $2 = reason (plain text, no double quotes)
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"%s"}}\n' "$1" "$2"
  exit 0
}

tool=$(field tool_name)

case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit)
    path=$(field file_path)
    [ -z "$path" ] && path=$(field notebook_path)
    if printf '%s' "$path" | grep -qiE '\.(uasset|umap)$'; then
      decide deny "GameMakerAgent: .uasset and .umap files are binary Unreal assets and break if edited as text. Describe the steps to do this in the Unreal Editor instead."
    fi
    if printf '%s' "$path" | grep -qiE '(Epic Games([\/]+)UE_[^\/]*|UE_[0-9][^\/]*([\/]+)Engine)([\/]|$)'; then
      decide deny "GameMakerAgent: this file is inside the Unreal Engine installation. Never change engine files; make the change in the project instead."
    fi
    ;;
  Bash|PowerShell)
    cmd=$(field command)
    if printf '%s' "$cmd" | grep -qiE '(^|[^A-Za-z0-9_-])(rm|rmdir|rd|del|erase|Remove-Item|ri)([[:space:]]|$)|git[[:space:]]+(clean|reset[[:space:]]+--hard|checkout[[:space:]]+--|restore)([[:space:]]|$)'; then
      decide ask "GameMakerAgent: this command deletes or discards files in your Unreal project. Check what it removes before you allow it."
    fi
    ;;
esac

exit 0
