---
name: gma-init
description: Set up an Unreal Engine project for GameMakerAgent. Creates CLAUDE.md, a Game Design Document, a task list, and Unreal-ready .gitignore and .gitattributes files. Run this once in the root folder of an Unreal project.
disable-model-invocation: true
argument-hint: "[short description of your game]"
allowed-tools: Read(${CLAUDE_SKILL_DIR}/templates/**)
---

Set up the current folder as an Unreal Engine project that works well with the GameMakerAgent agents. Reply in the language the user writes in, and explain each step simply; the user may be a beginner.

The user's description of their game (may be empty): $ARGUMENTS

Templates for this skill are in `${CLAUDE_SKILL_DIR}/templates/`.

## Rules for every file

- Never overwrite an existing file silently. If a file already exists, show the user what you would add or change and ask first.
- Create files only in the project root and its `Docs/` folder.
- At the end, list every file you created or changed.

## Steps

1. **Find the project.** Look for a `*.uproject` file in the current folder.
   - If there is none, stop. Tell the user this skill must be run inside an Unreal project folder (the one that contains the `.uproject` file) and explain how to open Claude Code there (open a terminal in that folder, then run `claude`).
   - If there are several, ask which one to use.

2. **Gather facts.** Read the `.uproject` file and note:
   - Project name (the file name without `.uproject`).
   - Engine version (`EngineAssociation`).
   - Modules and enabled plugins.
   - Whether a `Source/` folder exists (C++ project) or not (Blueprint-only project).
   If `Source/<ProjectName>/` exists, note the folder layout and the `<PROJECTNAME>_API` macro.

3. **Ask about the game** if `$ARGUMENTS` is empty: one short question, "In one or two sentences, what game are you making?". Accept "I don't know yet" and leave placeholders.

4. **Write `CLAUDE.md`** in the project root, filled in from the facts above:

   ```markdown
   # <ProjectName>

   ## About the game
   <one or two sentences from the user, or "TBD">
   Design: Docs/GDD.md. Feature specs: Docs/Features/. Tasks: Docs/Tasks.md.

   ## Project facts
   - Engine: Unreal Engine <version>
   - Project type: C++ / Blueprint-only
   - Main module: <ModuleName> (export macro <PROJECTNAME>_API)
   - Platform: Windows

   ## Team workflow (GameMakerAgent)
   - game-designer writes a spec in Docs/Features/ before a feature is built.
   - programmer builds it; work is done only when it compiles.
   - qa reviews the change against the spec's acceptance criteria.
   - producer keeps Docs/Tasks.md up to date.

   ## Conventions
   - Follow Unreal Engine naming conventions (A/U/F/E/I prefixes, b for booleans).
   - Put new C++ classes in Source/<ModuleName>/ following the existing layout.
   - Expose tunable values to the editor with UPROPERTY(EditAnywhere).
   - Do not edit .uasset or .umap files directly; describe editor steps instead.
   - Never delete Binaries/, Intermediate/, Saved/ or DerivedDataCache/ without asking.

   ## Build
   - Build from the editor with Live Coding (Ctrl+Alt+F11) or from Visual Studio.
   ```

   For a Blueprint-only project, write "Project type: Blueprint-only", drop the module line, and add: "To add C++ later, use Tools > New C++ Class in the editor."

5. **Create the design documents** from the templates:
   - `Docs/GDD.md` from `templates/GDD.md`. Replace `<Game title>` with the project name, and fill in the pitch from the user's description if there is one.
   - `Docs/Tasks.md` from `templates/Tasks.md`.
   - An empty `Docs/Features/` folder (create a `Docs/Features/README.md` with one line: "One spec per feature, written by the game-designer agent.").

6. **Version control files.** Check whether the folder is a git repository (`git rev-parse --is-inside-work-tree`).
   - Explain in one sentence what each file does, then offer to create `.gitignore` from `templates/gitignore.txt` and `.gitattributes` from `templates/gitattributes.txt`. Create them only after the user agrees.
   - `.gitattributes` stores Unreal's large binary files with Git LFS. Check `git lfs version`. If Git LFS is missing, tell the user to install it from https://git-lfs.com and then run `git lfs install` once; do not install it yourself.
   - If the folder is not a git repository, still offer the files, and mention that the user can turn the folder into a repository later.

7. **Finish** with a short summary: the files you created, and three example requests the user can try next:
   - "Use the game-designer agent to design a sprint ability."
   - "/game-maker-agent:new-feature sprint ability"
   - "Use the producer agent to plan my first playable milestone."
