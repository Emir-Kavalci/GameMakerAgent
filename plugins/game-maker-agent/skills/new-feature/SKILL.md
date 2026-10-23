---
name: new-feature
description: Take one gameplay feature from idea to reviewed code with the GameMakerAgent team - spec by game-designer, code by programmer, review by qa, task list update by producer - with the user approving each step.
disable-model-invocation: true
argument-hint: "<feature idea, e.g. sprint ability>"
---

Run the GameMakerAgent team workflow for one feature. Reply in the language the user writes in. The user may be a beginner, so before each step say in one sentence which teammate works next and why.

Feature idea: $ARGUMENTS

If the feature idea is empty, ask the user for it in one short question and stop until they answer.

Delegate each step to the named subagent with the Agent tool, giving it the feature name, the relevant file paths and anything the user said. Subagents don't see this conversation, so include everything they need in the prompt. Stop after each step marked **Checkpoint** and wait for the user.

## Step 0: Check the project

Make sure the current folder contains a `*.uproject` file. If `CLAUDE.md` or `Docs/GDD.md` is missing, suggest running `/game-maker-agent:gma-init` first, and continue only if the user wants to.

## Step 1: Spec (game-designer)

Ask the `game-maker-agent:game-designer` agent to write `Docs/Features/<FeatureName>.md` for this idea, using `Docs/GDD.md` for context. If a spec for this feature already exists, have it review and update that one instead.

Show the user the spec's goal and acceptance criteria.

**Checkpoint:** ask the user to approve the spec or ask for changes. Loop on Step 1 until they approve.

## Step 2: Code (programmer)

Ask the `game-maker-agent:programmer` agent to implement the approved spec, naming the spec file, and to report which files it changed. Tell it not to build yet; the build happens at the checkpoint below.

**Checkpoint (build):** don't send the user to Visual Studio; beginners get lost there.
1. Ask the user to close the Unreal Editor if it is open (File > Save All first), and to say when it is closed.
2. Run the build yourself with the command from the project's `CLAUDE.md` (Build section). If it has none, find it the way the programmer agent's instructions describe: `"<EngineDir>/Engine/Build/BatchFiles/Build.bat" <ProjectName>Editor Win64 Development -Project="<full path to .uproject>" -WaitMutex`. Tell the user it can take a few minutes.
3. If the build fails, send the first error to the `game-maker-agent:programmer` agent to fix, then build again. After three failed attempts, stop and explain the situation to the user.
4. Continue when the output says `Result: Succeeded`.

## Step 3: Review (qa)

Ask the `game-maker-agent:qa` agent to review the change against the spec's acceptance criteria and produce its QA report and manual test plan. The editor is still closed after the build, so QA skips its optional editor check here; the user's editor test below covers it.

- If the verdict is "Needs fixes", show the problems, and with the user's agreement send the Blocker and Major problems to the `game-maker-agent:programmer` agent. Then repeat the build checkpoint and Step 3. Stop after two fix rounds and let the user decide how to continue.
- If the verdict is "Ready to test in editor", show the manual test plan.

**Checkpoint (editor test):** tell the user to open the project in the Unreal Editor now (double-click the `.uproject` file), follow the test plan, and report what happened. Remind them to use File > Save All before closing the editor. Problems they find go back to the programmer, like QA problems.

## Step 4: Wrap up (producer)

Ask the `game-maker-agent:producer` agent to mark the feature as done in `Docs/Tasks.md` (adding it if it is missing) and to suggest the next task.

Finish with a short summary: the spec file, the changed code files, the QA verdict, and the suggested next task. If the project is a git repository, suggest committing the work now, with a one-line commit message.
