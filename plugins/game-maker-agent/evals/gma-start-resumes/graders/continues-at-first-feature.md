---
type: llm
---

The project's progress file says steps 1 to 4 of the getting-started guide are done (computer check, project, setup, meet the team) and step 5, the first feature, is next. The game's design document lists coin pickup and the coin count as already done in C++ but with no UI yet, and checkpoints, speed pads and menus as not finished.
PASS if the reply continues with the first feature: it does not redo the computer check, project setup or team introduction, it offers a few small first features that fit this game, and it tells the user to type /game-maker-agent:new-feature with the chosen idea.
FAIL if it starts over from the computer check or setup, runs setup itself, suggests building the coin pickup or the coin counting again as if they did not exist (showing the existing coin count on screen is a new feature and is fine), or doesn't tell the user how to start the feature.
