---
name: gma-init
description: Set up an Unreal Engine project for GameMakerAgent by creating a CLAUDE.md file that describes the project to Claude. Run this once in the root folder of an Unreal project.
disable-model-invocation: true
argument-hint: "[short description of your game]"
---

Set up the current folder as an Unreal Engine project that works well with the GameMakerAgent agents. Reply in the language the user writes in, and explain each step simply; the user may be a beginner.

The user's description of their game (may be empty): $ARGUMENTS

## Steps

1. **Find the project.** Look for a `*.uproject` file in the current folder.
   - If there is none, stop. Tell the user this command must be run inside an Unreal project folder (the one that contains the `.uproject` file) and explain how to open Claude Code there.
   - If there are several, ask which one to use.

2. **Gather facts.** Read the `.uproject` file and note:
   - Project name (the file name without `.uproject`).
   - Engine version (`EngineAssociation`).
   - Modules and enabled plugins.
   - Whether a `Source/` folder exists (C++ project) or not (Blueprint-only project).
   If `Source/<ProjectName>/` exists, note the folder layout and the `<PROJECTNAME>_API` macro.

3. **Check for an existing CLAUDE.md.** If `CLAUDE.md` already exists in the project root, show the user what you would add and ask before changing it. Never overwrite it silently.

4. **Ask about the game** if `$ARGUMENTS` is empty: one short question, "In one or two sentences, what game are you making?". Accept "I don't know yet" and leave a placeholder.

5. **Write `CLAUDE.md`** in the project root with these sections, filled in from the facts above:

   ```markdown
   # <ProjectName>

   ## About the game
   <one or two sentences from the user, or "TBD">

   ## Project facts
   - Engine: Unreal Engine <version>
   - Project type: C++ / Blueprint-only
   - Main module: <ModuleName> (export macro <PROJECTNAME>_API)
   - Platform: Windows

   ## Conventions
   - Follow Unreal Engine naming conventions (A/U/F/E/I prefixes, b for booleans).
   - Put new C++ classes in Source/<ModuleName>/ following the existing layout.
   - Expose tunable values to the editor with UPROPERTY(EditAnywhere).
   - Do not edit .uasset or .umap files directly; describe editor steps instead.
   - Never delete Binaries/, Intermediate/, Saved/ or DerivedDataCache/ without asking.

   ## Build
   - Build from the editor with Live Coding (Ctrl+Alt+F11) or from Visual Studio.
   ```

6. **Check `.gitignore`.** If the project is a git repository and has no `.gitignore`, offer to create one that ignores `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, `.vs/` and `*.sln`. Ask before creating it.

7. **Finish** with a short summary: what you created, and that the user can now ask for help, for example "Use the programmer agent to add a sprint ability to my character".
