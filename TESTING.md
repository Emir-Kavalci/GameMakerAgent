# Testing GameMakerAgent

GameMakerAgent has six kinds of checks. Run them before you publish a change to an agent, a skill or the safety hook.

| Check | What it tests | Cost | Runs on GitHub |
| --- | --- | --- | --- |
| `claude plugin validate` | Manifests and the agent, skill and hook files are well-formed | Free | Yes, on every push |
| `tests/test-guard.sh` | The safety hook blocks and allows the right tool calls | Free | Yes, on every push |
| `tests/test_bridge.py` | The Unreal Editor bridge speaks MCP correctly; the log reader and C++ header scan work (no editor needed) | Free | Yes, on every push |
| `tests/test_blueprint_text.py` | Blueprint export text is turned into the right readable steps (no editor needed) | Free | Yes, on every push |
| Bridge with a live editor | The bridge reads and changes a real open project | Free | No, run it yourself (see below) |
| Eval suite (`claude plugin eval`) | Each agent and skill behaves the way its instructions say | Uses the Claude plan of whoever runs it | No, run it yourself |

GameMakerAgent itself is free. People who install the plugin never run these tests and are never charged for them. The eval suite only runs when a developer of this repository starts it by hand, and then it counts against that developer's own Claude plan. Nothing runs it automatically.

## Validate and hook tests

From the repository root (on Windows, use Git Bash):

```bash
claude plugin validate .
claude plugin validate plugins/game-maker-agent
bash tests/test-guard.sh
python tests/test_bridge.py
python tests/test_blueprint_text.py
```

## Unreal Editor bridge with a live editor

The bridge (`plugins/game-maker-agent/mcp/`) can only be fully tested against a real editor, so this is a manual check on Windows:

1. Open an Unreal 5.7 test project whose editor connection is on (see the README).
2. In a terminal in that project folder, start Claude Code with your working copy: `claude --plugin-dir <repo>/plugins/game-maker-agent`.
3. Ask: "Is the Unreal Editor connected?", then "List the Blueprints in my project", "What are the default values of <a Blueprint>?" and "List the actors in the open level".
   Then "Read <a Blueprint> and explain its logic": open the same Blueprint in the editor and check that the steps, branches and values match the graph. Try an Actor, a Widget and an Anim Blueprint, and one whose parent class is your C++.
   Then "Show me the level" and "Take a screenshot of <an actor in the level>" (your camera and selection must not change), with the editor behind other windows, and "Are there errors in the Output Log?". Press Play, walk around, stop, and ask "What did the log say while I played?". If your game can reload its level during play (a restart key, OpenLevel), reload once before you stop: the answer must still cover the whole play session and mention the level load.
   Then "What are the values of <a Blueprint built on your C++ class>?": protected C++ properties must be listed under their C++ names.
   Then "Which key is Interact?" (or another action): the answer must come from the project's Input Mapping Context, listed with its keys.
4. Ask for a small change (for example "set <Blueprint>'s <value> to 2"). Claude Code must show you the script and wait for your OK before it runs. Afterwards ask Claude to set it back, or close the editor without saving.

The eval suite can't cover the bridge, because eval runs have no editor.

## Eval suite

The cases live in `plugins/game-maker-agent/evals/`, one folder per case. Each case:

1. builds a small fake Unreal 5.7 C++ project called **Skyhop** with `evals/_fixtures/unreal-project.sh` (no real engine needed),
2. sends one realistic request, such as "Use the qa agent to review SpeedPad.cpp",
3. grades the result with fixed checks (files created or untouched, text patterns) and a few judge-model checks.

| Case | What it proves |
| --- | --- |
| `designer-writes-spec` | game-designer writes a spec with testable acceptance criteria and no code |
| `designer-imports-gdd` | game-designer brings the user's own design document into `Docs/GDD.md`, leaves the original untouched, lists gaps and a contradiction as open questions, and makes no suggestions when told not to |
| `level-designer-plans-level` | level-designer writes a level plan from the character's real values (double jump), with sizes and a playtest checklist, and creates no level or code files |
| `ui-ux-no-fake-options` | ui-ux-designer plans the menus in `Docs/UI.md` with gamepad navigation and leaves out multiplayer, which the game doesn't have |
| `programmer-new-class` | programmer follows the project's module layout, `_API` macro and Unreal header rules |
| `programmer-refuses-uasset` | `.uasset` files are never edited as text (agent rule; the safety hook itself is tested by `tests/test-guard.sh`) |
| `qa-finds-bug-read-only` | qa finds a real crash bug against the spec and changes no files |
| `producer-plans-milestone` | producer writes small tasks with owners and keeps finished work |
| `marketing-no-fake-features` | marketing refuses to advertise a feature the game doesn't have |
| `tech-artist-audit-read-only` | technical-artist finds badly named assets and changes nothing |
| `art-director-no-images` | art-director says it can't make images and offers a brief instead |
| `audio-director-no-audio` | audio-director says it can't make sound files and offers a brief instead |
| `asset-scout-license-check` | asset-scout rejects a NonCommercial model for a game that will be sold, accepts a CC BY one, records it with its credit line in `Docs/AssetCredits.md`, and marks it in the asset list |
| `asset-scout-ignores-injection` | asset-scout ignores an instruction hidden in text copied from an asset page, tells the user about it, and still rejects a NonCommercial model for a game that will be sold |
| `asset-scout-unclear-license` | asset-scout rejects an "editorial use only" model and one with no written license, and records neither |
| `designer-gdd-wants-suggestions` | after bringing in the user's document, game-designer gives at most five suggestions with reasons and writes none of them into the GDD before the user accepts |
| `designer-gdd-too-big` | game-designer keeps a design that is far too big for one person as written and names the scope risk once, without pushing changes |
| `gma-init-with-gdd-path` | gma-init given a design document path has the game-designer write `Docs/GDD.md` from it and leaves the original untouched |
| `producer-routes-asset-scout` | producer gives finding and importing ready-made models and sounds to asset-scout |
| `gma-start-resumes` | gma-start reads its progress file and continues at the first feature instead of repeating setup |
| `gma-start-new-project` | gma-start in a fresh project saves its progress and sends the user to gma-init without doing setup itself |
| `gma-init-sets-up-project` | gma-init writes CLAUDE.md with the right facts, the GDD and the task list |
| `gma-init-outside-project` | gma-init stops when the folder isn't an Unreal project |

The `new-feature` workflow isn't covered: it stops for the user at every checkpoint, so it is tested by hand on a real project.

### Run it

From `plugins/game-maker-agent/`:

```bash
# Quick check: every case once (about 2 USD with Sonnet)
claude plugin eval . --scaffold --trust-plugin --allow-tools Write Edit --ablation none --runs 1 -j 4 --model sonnet

# One case, three runs, after changing one agent
claude plugin eval . --case qa-finds-bug-read-only --scaffold --trust-plugin --allow-tools Write Edit --ablation none -j 3 --model sonnet
```

What the flags mean:

- `--scaffold` runs each case's `setup.sh`, which creates the fake project. Only use it on cases you have read.
- `--allow-tools Write Edit` lets agents write files inside the throwaway test folder. Bash isn't granted, because on native Windows the eval sandbox can't run shell commands, so cases never depend on Bash.
- `--ablation none` skips the "without the plugin" comparison. It is meaningless here, because the agents don't exist without the plugin.

Results go to `evals/results/` (ignored by git). Open the `report.html` there to see every check and the judge's reasons.

A single run is noisy. Before you decide that a change made an agent better or worse, run the affected case three times (the default).
