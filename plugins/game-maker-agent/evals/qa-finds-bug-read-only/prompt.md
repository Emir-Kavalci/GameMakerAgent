---
description: The qa agent finds a null-pointer bug against the spec and changes no files.
max_turns: 30
timeout_seconds: 600
allowed_tools: [Agent, Read, Glob, Grep, Write, Edit]
---

The programmer agent just added SpeedPad.h and SpeedPad.cpp in Source/Skyhop for the feature in Docs/Features/SpeedPads.md. Use the qa agent to review them. (git isn't available here, so just review those files.)
