---
type: llm
---

The folder is a fresh Unreal project (it has a .uproject file) that has not been set up for GameMakerAgent yet, and the user said the required tools are installed.
PASS if the reply treats the project step as done, explains briefly what project setup does, and asks the user to type /game-maker-agent:gma-init (with a sentence about their game) and then run /game-maker-agent:gma-start again.
FAIL if it tells the user to create a new Unreal project, says the tools are missing, or does the setup itself (writes CLAUDE.md or the design documents).
