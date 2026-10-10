# GameMakerAgent

A team of [Claude Code](https://code.claude.com) agents for people who make games alone with **Unreal Engine 5**.

A real game studio has programmers, designers, artists, QA testers and producers. A solo developer has to be all of them. GameMakerAgent gives Claude Code one agent per game-development role, so you can hand each kind of work to a specialist.

> **Status: early preview (v0.2.0).** Built for Unreal Engine 5.7 on Windows. Testing in a real Unreal project is in progress, so expect rough edges.

## What's included

### Agents

| Agent | Role |
| --- | --- |
| `game-designer` | Shapes your idea, keeps the Game Design Document (`Docs/GDD.md`) and writes a spec with acceptance criteria for each feature. Doesn't write code. |
| `programmer` | Writes and fixes Unreal Engine C++ gameplay code from the spec, explains compile errors, and follows your project's conventions. |
| `qa` | Reviews code changes against the spec and common Unreal pitfalls, and writes a manual test plan. Read-only: it reports problems but never edits your files. |
| `producer` | Breaks the game into small tasks in `Docs/Tasks.md`, assigns each to the right teammate, and helps you cut scope. |

The agent that writes code is never the one that reviews it.

### Skills (slash commands)

| Command | What it does |
| --- | --- |
| `/game-maker-agent:gma-init` | Run once inside your Unreal project. Creates `CLAUDE.md`, `Docs/GDD.md`, `Docs/Tasks.md`, and (if you agree) Unreal-ready `.gitignore` and `.gitattributes` files. |
| `/game-maker-agent:new-feature <idea>` | Takes one feature from idea to reviewed code: spec → code → your build → QA review → your editor test → task list update. You approve every step. |

Planned roles: Art Director, Technical Artist, Audio and Marketing.

## Install

You need [Claude Code](https://code.claude.com) installed.

In a Claude Code session, run:

```
/plugin marketplace add Emir-Kavalci/GameMakerAgent
/plugin install game-maker-agent@game-maker-agent
```

## Quick start

1. Open a terminal in your Unreal project folder (the one that contains the `.uproject` file) and start `claude`.
2. Run `/game-maker-agent:gma-init` and answer its question about your game.
3. Build your first feature: `/game-maker-agent:new-feature sprint ability`
4. Or talk to one teammate directly, for example: *"Use the producer agent to plan my first playable milestone."*

## Built with AI

GameMakerAgent is developed with the help of AI: the plugin files, agent instructions and documentation are written together with [Claude Code](https://code.claude.com). Every change is reviewed and tested by the maintainer before it is published.

## Disclaimer

GameMakerAgent is an independent community project. It is not made, endorsed or supported by Anthropic or Epic Games. "Unreal Engine" is a trademark of Epic Games, Inc. "Claude" is a trademark of Anthropic, PBC.

## License

[MIT](LICENSE)
