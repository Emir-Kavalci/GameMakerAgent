---
description: gma-init given a design document path hands the import to the game-designer, which writes Docs/GDD.md from it and leaves the original untouched.
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Agent, Read, Glob, Grep, Write, Edit]
---

/game-maker-agent:gma-init my GDD is in Design/MyGame.md
