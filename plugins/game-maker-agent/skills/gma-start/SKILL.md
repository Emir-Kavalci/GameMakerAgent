---
name: gma-start
description: A step-by-step getting-started guide for beginners - checks the computer (Unreal Engine, Visual Studio C++, Git), helps create an Unreal project, guides the user through project setup, introduces the agent team, and walks them through building a first small feature. Remembers progress in Docs/GettingStarted.md, so running it again continues where the user stopped.
disable-model-invocation: true
argument-hint: "[optional: what kind of game you want to make]"
allowed-tools: Bash(git --version), Bash(git lfs version), Bash(reg query *)
---

Guide a beginner from zero to their first working feature with GameMakerAgent. Reply in the language the user writes in. The user may never have used Unreal Engine, Visual Studio, Git or a terminal before, so:

- Do one step at a time. Say what the step is for in one sentence, then give numbered click-by-click instructions (window name, button name, what they should see after clicking).
- Explain every new term once, in plain words.
- After a step that the user does by hand, stop and wait until they say it is done or describe what they see.
- Never install, download or uninstall anything yourself. Tell the user what to install and where it comes from.
- Everything this guide asks for is free. If a choice would cost money (a paid Visual Studio edition, a paid asset), say so and offer the free option.

What the user wants to make (may be empty): $ARGUMENTS

## The progress file

When the current folder contains a `*.uproject` file, keep the progress in `Docs/GettingStarted.md` (create `Docs/` if needed). Create it as soon as you are in a project folder, after Step 0. Before the project exists there is nowhere to save, so the computer check and project creation are simply repeated quickly next time. If the user described their game, put it in the Notes line, so it isn't lost between runs.

```markdown
# Getting started with GameMakerAgent

- [ ] 1. Computer check
- [ ] 2. Unreal project
- [ ] 3. Project setup (/game-maker-agent:gma-init)
- [ ] 4. Meet the team
- [ ] 5. First feature (/game-maker-agent:new-feature)
- [ ] 6. Save your work (git commit)

Next step: <one sentence>
Notes: <anything to remember, for example the chosen first feature, or a tool that was missing>
```

Tick a step as soon as it is finished and update "Next step". This file only records the guide's progress; never put anything else in it.

## Step 0: Where are we?

1. If `Docs/GettingStarted.md` exists, read it. Greet the user, say in one line which steps are done, and continue with the first unticked step. Don't repeat finished steps unless the user asks.
2. Whether or not the file exists, check what is already there and tick those steps: a `*.uproject` file in the current folder means step 2 is done; a `CLAUDE.md` that mentions GameMakerAgent plus a `Docs/GDD.md` mean step 3 is done.
3. On a first run, give a three-line welcome: what GameMakerAgent is (a team of AI teammates, one per game-development role), what this guide will do (the six steps above), and that it can be stopped at any time and continued later by typing `/game-maker-agent:gma-start` again.

## Step 1: Computer check

Check, and report each item as found or missing:

- **Unreal Engine.** Run `reg query "HKLM\SOFTWARE\EpicGames\Unreal Engine" //s //v InstalledDirectory` (write the doubled slashes: Claude Code's shell on Windows turns a single `/s` into a file path and the command fails) and list the installed versions. If it finds nothing, also look for `C:/Program Files/Epic Games/UE_*` with Glob. GameMakerAgent is built and tested for Unreal Engine 5.7; if only another 5.x version is installed, say it may work but 5.7 is the tested one, and let the user choose.
- **Visual Studio with C++ for games** (needed to build C++ projects). Run `"C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe" -products "*" -requires Microsoft.VisualStudio.Workload.NativeGame -property displayName`. A name in the output means Visual Studio with the "Game development with C++" workload is installed. Empty output means it is missing or the workload isn't ticked; if `vswhere.exe` doesn't exist, Visual Studio isn't installed.
- **Git and Git LFS** (save points for the project, and how big Unreal files are stored). Run `git --version` and `git lfs version`.

If a check can't run (the command is blocked or not allowed), don't report the item as missing: say you couldn't check it and ask the user. If the user says an item is installed but your check didn't find it (for example Unreal on another drive), take their word and continue; only an item that both your check and the user say is missing counts as missing. Reading folders outside the project can make Claude Code ask for permission; tell the user that is a read-only look.

If something is missing, give its free install path and the key choices:
- Unreal Engine: install the Epic Games Launcher from https://www.unrealengine.com, sign in with a free Epic account, then Unreal Engine > Library > the "+" next to Engine Versions > choose 5.7 > Install. Warn that it needs a lot of disk space (plan for about 100 GB free) and can take an hour or more to download.
- Visual Studio Community (free): https://visualstudio.microsoft.com. Use the version Epic lists for Unreal Engine 5.7 (Visual Studio 2022; if the site offers a newer one, check Epic's "Setting Up Visual Studio" page first). In the installer tick the "Game development with C++" workload; in the panel on the right keep the MSVC build tools and a Windows SDK ticked. If Visual Studio is already installed, open the Visual Studio Installer > Modify > Workloads and tick it there.
- Git: https://git-scm.com (default options are fine; Git for Windows already includes Git LFS). If `git lfs version` still fails, install it from https://git-lfs.com.

Git is recommended but not required to continue. Unreal Engine and Visual Studio are required for the rest of the guide. If either is missing, stop here, and tell the user to run `/game-maker-agent:gma-start` again when it is installed.

## Step 2: Unreal project

If the current folder has a `*.uproject` file, this step is done; say which project it is.

Otherwise, check whether the user already has a project they want to use. If yes, tell them to close this Claude Code session, open a terminal in that project's folder (the one with the `.uproject` file: in File Explorer, open the folder, click the address bar, type `cmd`, press Enter), run `claude`, and type `/game-maker-agent:gma-start` again.

If not, walk them through creating one:
1. Open the Epic Games Launcher > Unreal Engine > Library, and click Launch under 5.7.
2. In the Unreal Project Browser choose Games > Third Person.
3. On the right, set Project Defaults to **C++** (GameMakerAgent's programmer writes C++), leave the rest as it is.
4. Choose a short project location without spaces or special characters (for example `C:\Games`) and a project name with letters only (for example `MyFirstGame`). Long paths cause build errors in Unreal. Unreal puts the project in a new folder with the project's name, here `C:\Games\MyFirstGame`.
5. Click Create. Warn them that the first time takes long: Unreal builds the C++ code and then prepares shaders. The editor can look frozen for 10 minutes or more; that is normal, don't close it. Visual Studio may also open by itself; they can close it, Claude runs the builds.
6. When the editor is open and they can see the level, close the editor (File > Exit). Then open a terminal in the project folder, the one with the `.uproject` file (`C:\Games\MyFirstGame` in the example), as described above, run `claude`, and type `/game-maker-agent:gma-start` again.

Stop here until the user is in the project folder.

## Step 3: Project setup

If `CLAUDE.md` mentions GameMakerAgent and `Docs/GDD.md` exists, setup is done (the user ran it since last time): tick step 3, say so in one line, and go on to Step 4.

Explain in two sentences what `/game-maker-agent:gma-init` does: it writes `CLAUDE.md` (what the agents need to know about this project), a design document and a task list, and offers Git files and the editor connection. Recommend saying yes to the editor connection: then the agents can look at the real project instead of guessing, and every change through it still needs the user's approval.

Then ask the user to type `/game-maker-agent:gma-init` followed by one sentence about their game (use `$ARGUMENTS` in the example if they gave it), and to type `/game-maker-agent:gma-start` again when it is done. Commands that change files only start when the user types them, so you don't run it yourself.

## Step 4: Meet the team

Read `CLAUDE.md` and `Docs/GDD.md`. Then explain, in at most ten short lines:
- the core loop of working with the team: **game-designer** writes a spec (what to build and how to check it), **programmer** builds it, **qa** reviews it, the user tests it in the editor, **producer** keeps the task list;
- the other teammates in one line each: level-designer, ui-ux-designer, art-director, technical-artist, audio-director, marketing;
- that the user talks to a teammate by name, for example "Use the producer agent to plan my first milestone";
- where the documents are: `Docs/GDD.md`, `Docs/Features/`, `Docs/Tasks.md`;
- that agents can't make images, 3D models or sound files; they plan, write code and scripts, and review.

Tick step 4.

## Step 5: First feature

Offer three very small first features that fit the project. Read `Docs/GDD.md` and `Docs/Features/` first, and never offer a feature they list as done or in progress. For a project made from the Third Person template (it has a `Content/ThirdPerson/` folder) whose GDD doesn't list them yet:
1. A collectible coin: walk into it, it disappears, a counter goes up (a good first feature: one new C++ class and one Blueprint).
2. Sprint: hold a key to run faster.
3. A jump pad: step on it and get launched up.
For any other project, pick three ideas of the same size from its `Docs/GDD.md`. Recommend the first one that isn't built yet, and let the user choose. Write the choice in the Notes line.

Before they start, explain what will happen, so no step surprises them:
- The team works in steps and stops at each checkpoint for the user's OK.
- For the build, the user closes the Unreal Editor (File > Save All first), and Claude runs the build; it takes a few minutes.
- Then the user opens the editor again, presses Play, and checks the test steps QA wrote.
- Using the agents counts toward the user's own Claude plan, like any Claude Code conversation; a small feature like this is a normal amount of use.

In the same message, show the exact command to type, filled in with your recommended idea, `/game-maker-agent:new-feature <idea>`, and ask the user to type it (with their chosen idea), and `/game-maker-agent:gma-start` again when the feature works in the editor. When they come back and confirm it works, tick step 5. If it didn't work, help them describe what happened to the programmer agent, and keep step 5 open.

## Step 6: Save your work

Explain what a commit is: a save point the project can always go back to. Before any commit, check:
- `.gitignore` exists and lists `Binaries/` and `Intermediate/`. Without it Git would save gigabytes of build files. If it is missing, ask the user to run `/game-maker-agent:gma-init` again and accept the Git files, then come back.
- If `.gitattributes` exists (it stores Unreal's big files with Git LFS), `git lfs version` works. If Git LFS is missing, help them install it first (see Step 1); otherwise the big files go into normal Git history and the repository grows fast.

Then:
- If the folder is a Git repository (`git rev-parse --is-inside-work-tree`), show `git status --short`. If there is nothing to commit (for example the new-feature workflow already committed), say the work is already saved and tick the step. Otherwise tell the user the two commands, `git add -A` and `git commit -m "First feature: <name>"`, and offer to run them after they agree.
- If it isn't a repository, explain that Git lets them go back if something breaks, and offer to set it up with `git init`, `git lfs install` (this only turns Git LFS on for this computer; it installs nothing) and the first commit. Run these only after the user agrees.

Tick step 6, and finish with:
- a short congratulation and what they built,
- three good next requests (for example: "Use the game-designer agent to shape my game idea in Docs/GDD.md", "Use the producer agent to plan my first playable milestone", "/game-maker-agent:new-feature <a next idea from the GDD>"),
- where to get help: https://github.com/Emir-Kavalci/GameMakerAgent/issues for problems with the agents.
