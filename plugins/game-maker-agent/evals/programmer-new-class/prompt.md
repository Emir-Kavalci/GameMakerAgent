---
description: The programmer agent adds a C++ class that follows the project's layout and Unreal conventions.
max_turns: 30
timeout_seconds: 600
allowed_tools: [Agent, Read, Glob, Grep, Write, Edit]
---

Use the programmer agent to add a C++ checkpoint actor called ACheckpoint: when the player character overlaps it, it stores the checkpoint's location as the player's respawn point. Don't build, I'll do that later.
