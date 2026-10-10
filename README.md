# GameMakerAgent

A team of [Claude Code](https://code.claude.com) agents for people who make games alone with **Unreal Engine 5**.

A real game studio has programmers, designers, artists, QA testers and producers. A solo developer has to be all of them. GameMakerAgent gives Claude Code one agent per game-development role, so you can hand each kind of work to a specialist.

> **Status: early preview (v0.1.0).** Only the first agent is included. Tested on Windows with Unreal Engine 5.7.

## What's included

| Component | What it does |
| --- | --- |
| `programmer` agent | Writes and fixes Unreal Engine C++ gameplay code, explains compile errors, and follows your project's conventions. |
| `/game-maker-agent:gma-init` | Run once inside your Unreal project. Creates a `CLAUDE.md` that tells Claude about your project. |

Planned roles: Game Designer, QA, Producer, then Art Director, Technical Artist, Audio and Marketing.

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
3. Ask for help, for example: *"Use the programmer agent to add a sprint ability to my character."*

## Built with AI

GameMakerAgent is developed with the help of AI: the plugin files, agent instructions and documentation are written together with [Claude Code](https://code.claude.com). Every change is reviewed and tested by the maintainer before it is published.

## Disclaimer

GameMakerAgent is an independent community project. It is not made, endorsed or supported by Anthropic or Epic Games. "Unreal Engine" is a trademark of Epic Games, Inc. "Claude" is a trademark of Anthropic, PBC.

## License

[MIT](LICENSE)
