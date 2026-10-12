# GameMakerAgent

A team of [Claude Code](https://code.claude.com) agents for people who make games alone with **Unreal Engine 5**.

A real game studio has programmers, designers, artists, QA testers and producers. A solo developer has to be all of them. GameMakerAgent gives Claude Code one agent per game-development role, so you can hand each kind of work to a specialist.

> **Status: early preview (v0.5.0).** Built for Unreal Engine 5.7 on Windows. The core feature workflow (designer, programmer, QA, producer) has been tested end to end on a real Unreal Engine 5.7 C++ project, and every agent has automated behavior tests (see [TESTING.md](TESTING.md)). Expect rough edges.

## What's included

### Agents

**Core team: builds the game**

| Agent | Role |
| --- | --- |
| `game-designer` | Shapes your idea, keeps the Game Design Document (`Docs/GDD.md`) and writes a spec with acceptance criteria for each feature. Doesn't write code. |
| `programmer` | Writes and fixes Unreal Engine C++ gameplay code from the spec, explains compile errors, and follows your project's conventions. |
| `qa` | Reviews code changes against the spec and common Unreal pitfalls, and writes a manual test plan. Read-only: it reports problems but never edits your files. |
| `producer` | Breaks the game into small tasks in `Docs/Tasks.md`, assigns each to the right teammate, and helps you cut scope. |

The agent that writes code is never the one that reviews it.

**Production and launch: plans art, sound and promotion**

| Agent | Role |
| --- | --- |
| `art-director` | Defines the visual style (`Docs/ArtBible.md`), lists every art asset (`Docs/AssetList.md`), writes briefs and prompts for artists or image tools, and reviews your screenshots. |
| `technical-artist` | Naming rules, folder structure, polygon and texture budgets, import and material setup, Content folder audits, and Unreal Editor Python / Blender scripts. |
| `audio-director` | Plans sound effects and music (`Docs/AudioList.md`), writes briefs and prompts for audio, and explains how to set sounds up in Unreal. |
| `marketing` | Store page text, trailer shot list, devlogs, press kit and launch plan in `Docs/Marketing/`. Only claims what is really in your game, and never publishes anything itself. |

**What these agents can't do:** Claude doesn't create images, 3D models, music or sound files. These agents plan, describe, write briefs and prompts for the people or tools you choose, write scripts, and review results.

### Skills (slash commands)

| Command | What it does |
| --- | --- |
| `/game-maker-agent:gma-init` | Run once inside your Unreal project. Creates `CLAUDE.md`, `Docs/GDD.md`, `Docs/Tasks.md`, and (if you agree) Unreal-ready `.gitignore` and `.gitattributes` files and the Unreal Editor connection. |
| `/game-maker-agent:new-feature <idea>` | Takes one feature from idea to reviewed code: spec → code → your build → QA review → your editor test → task list update. You approve every step. |

### Unreal Editor connection (optional, Windows)

GameMakerAgent can connect to your open Unreal Editor. Then the agents can look at the real project instead of guessing: read a Blueprint's default values or one placed actor's values, list assets with their real types, and list the actors in the open level. With your approval for each script, they can also change things the safe way, through the editor (for example set a Blueprint value or rename assets without breaking references).

- **Turn it on:** run `/game-maker-agent:gma-init` and say yes to the editor connection. It enables Unreal's built-in Python Editor Script Plugin and its "Enable Remote Execution" setting. Or do it yourself: Edit > Plugins > "Python Editor Script Plugin", then Edit > Project Settings > Plugins > Python > "Enable Remote Execution?".
- **Check it:** with the editor open, ask Claude *"Is the Unreal Editor connected?"*.
- **Nothing to install:** the connection runs on the Python that ships inside Unreal Engine and uses Epic's own remote execution. It only listens on your computer (127.0.0.1).
- **You stay in control:** reading is free of prompts; every script that could change the project is shown to you first and needs your OK.
- On macOS and Linux the connection isn't supported yet, and Claude Code lists it as a server that failed to start; the rest of the plugin works.

### Safety guard

Inside an Unreal project (a folder with a `.uproject` file), the plugin checks every file edit and shell command Claude is about to run:

- It blocks text edits to `.uasset` and `.umap` files. These are binary, and editing them as text breaks them. Claude describes the editor steps instead.
- It blocks changes to files inside the Unreal Engine installation folder.
- It always asks you before a command that deletes or discards files (`rm`, `del`, `Remove-Item`, `git clean`, `git reset --hard` and similar), even if you have allowed Claude to run commands without asking.
- It always asks you before a Python script runs inside the Unreal Editor.

In other folders only the editor-script rule applies. On Windows it needs Git Bash, which comes with [Git for Windows](https://git-scm.com/downloads/win). Without it the guard can't run, and Claude Code shows a hook error instead.

Planned: more roles and workflows, and later other engines (Unity, Godot).

## Install

You need [Claude Code](https://code.claude.com) installed.

In a Claude Code session, run:

```
/plugin marketplace add Emir-Kavalci/GameMakerAgent
/plugin install game-maker-agent@game-maker-agent
```

Restart Claude Code after installing.

To update later, run `/plugin marketplace update game-maker-agent`, then `/plugin update game-maker-agent@game-maker-agent`, and restart Claude Code. See what changed in the [changelog](CHANGELOG.md).

## Cost

GameMakerAgent is free and open source. It has no paid tier, no API keys and no accounts of its own.

The agents run inside Claude Code, so using them counts toward your own Claude plan's usage, the same as any other Claude Code conversation. The plugin adds no extra charge.

## Quick start

1. Open a terminal in your Unreal project folder (the one that contains the `.uproject` file) and start `claude`.
2. Run `/game-maker-agent:gma-init` and answer its question about your game.
3. Build your first feature: `/game-maker-agent:new-feature sprint ability`
4. Or talk to one teammate directly, for example: *"Use the producer agent to plan my first playable milestone."*

## Feedback and contributing

Did an agent do the wrong thing? [Open an issue](https://github.com/Emir-Kavalci/GameMakerAgent/issues/new/choose) and say what you asked and what happened; these reports are the main way the agents get better. To change the plugin yourself, see [CONTRIBUTING.md](CONTRIBUTING.md). Security problems go through [SECURITY.md](SECURITY.md), not public issues.

## Built with AI

GameMakerAgent is developed with the help of AI: the plugin files, agent instructions and documentation are written together with [Claude Code](https://code.claude.com). Every change is reviewed and tested by the maintainer before it is published.

## Disclaimer

GameMakerAgent is an independent community project. It is not made, endorsed or supported by Anthropic or Epic Games. "Unreal Engine" is a trademark of Epic Games, Inc. "Claude" is a trademark of Anthropic, PBC.

## License

[MIT](LICENSE)
