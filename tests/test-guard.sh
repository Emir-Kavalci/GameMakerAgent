#!/usr/bin/env bash
# Tests for plugins/game-maker-agent/hooks/guard.sh. No model calls; free to run.
# Usage: bash tests/test-guard.sh

here=$(cd "$(dirname "$0")" && pwd)
guard="$here/../plugins/game-maker-agent/hooks/guard.sh"

unreal=$(mktemp -d)
touch "$unreal/MyGame.uproject"
other=$(mktemp -d)
trap 'rm -rf "$unreal" "$other"' EXIT

fail=0
# check <name> <project dir> <expected: deny|ask|none> <hook input json>
check() {
  out=$(printf '%s' "$4" | CLAUDE_PROJECT_DIR="$2" bash "$guard")
  code=$?
  got=none
  case "$out" in
    *'"permissionDecision":"deny"'*) got=deny ;;
    *'"permissionDecision":"ask"'*) got=ask ;;
  esac
  if [ "$code" -ne 0 ] || [ "$got" != "$3" ]; then
    echo "FAIL  $1 (expected $3, got $got, exit $code)"
    fail=1
  else
    echo "ok    $1"
  fi
}

edit() { printf '{"hook_event_name":"PreToolUse","tool_name":"%s","tool_input":{"file_path":"%s","old_string":"a","new_string":"b"}}' "$1" "$2"; }
shell() { printf '{"hook_event_name":"PreToolUse","tool_name":"%s","tool_input":{"command":"%s","description":"x"}}' "$1" "$2"; }

check "edit .uasset is denied"            "$unreal" deny "$(edit Edit 'C:\\Game\\Content\\BP_Gem.uasset')"
check "write .umap is denied"             "$unreal" deny "$(edit Write '/home/me/Game/Content/Maps/Main.umap')"
check "uppercase .UASSET is denied"       "$unreal" deny "$(edit Edit 'Content/Hero.UASSET')"
check "engine file (Windows) is denied"   "$unreal" deny "$(edit Edit 'C:\\Program Files\\Epic Games\\UE_5.7\\Engine\\Source\\Runtime\\Engine\\Classes\\GameFramework\\Actor.h')"
check "engine file (custom dir) is denied" "$unreal" deny "$(edit Write 'D:/UE_5.7/Engine/Config/BaseEngine.ini')"
check "project .cpp is allowed"           "$unreal" none "$(edit Edit 'C:\\Game\\Source\\MyGame\\Gem.cpp')"
check "project Docs file is allowed"      "$unreal" none "$(edit Write 'Docs/Features/Sprint.md')"
check "rm asks"                           "$unreal" ask  "$(shell Bash 'rm -rf Intermediate')"
check "Remove-Item asks"                  "$unreal" ask  "$(shell PowerShell 'Remove-Item -Recurse Binaries')"
check "chained del asks"                  "$unreal" ask  "$(shell Bash 'cd Saved && del /s *.log')"
check "git clean asks"                    "$unreal" ask  "$(shell Bash 'git clean -fdx')"
check "git reset --hard asks"             "$unreal" ask  "$(shell Bash 'git reset --hard HEAD')"
check "build command is allowed"          "$unreal" none "$(shell Bash '\\"C:/Program Files/Epic Games/UE_5.7/Engine/Build/BatchFiles/Build.bat\\" MyGameEditor Win64 Development')"
check "git status is allowed"             "$unreal" none "$(shell Bash 'git status')"
check "word 'model' is not 'del'"         "$unreal" none "$(shell Bash 'grep -r model Source')"
check "outside Unreal: .uasset ignored"   "$other"  none "$(edit Edit 'Content/BP_Gem.uasset')"
check "outside Unreal: rm ignored"        "$other"  none "$(shell Bash 'rm -rf build')"
check "editor Python asks"                "$unreal" ask  '{"hook_event_name":"PreToolUse","tool_name":"mcp__plugin_game-maker-agent_unreal__unreal_run_python","tool_input":{"code":"print(1)"}}'
check "outside Unreal: editor Python asks" "$other" ask  '{"hook_event_name":"PreToolUse","tool_name":"mcp__plugin_game-maker-agent_unreal__unreal_run_python","tool_input":{"code":"print(1)"}}'
check "editor read-only tool is allowed"  "$unreal" none '{"hook_event_name":"PreToolUse","tool_name":"mcp__plugin_game-maker-agent_unreal__unreal_list_assets","tool_input":{}}'

if [ "$fail" -ne 0 ]; then
  echo "Some guard tests failed."
  exit 1
fi
echo "All guard tests passed."
