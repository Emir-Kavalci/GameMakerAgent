# Changelog

All notable changes to GameMakerAgent are listed here. Versions follow [Semantic Versioning](https://semver.org/); while the version starts with `0.`, any release may change how agents behave.

To update an installed copy, run `/plugin marketplace update game-maker-agent` in Claude Code, then `/plugin update game-maker-agent@game-maker-agent`, and restart Claude Code.

## [Unreleased]

### Added
- `unreal_read_blueprint`: reads a Blueprint (Actor, Widget or Anim Blueprint) as text: parent class, components, variables with defaults, and every graph as indented steps with the values wired into each node. It marks events declared in C++ and C++ functions the Blueprint calls. The editor exports the Blueprint as T3D text and the bridge turns it into steps, so nothing extra is installed.
- `unreal_list_assets` shows each Blueprint's parent class and can filter by it (`parent_class`), to find the Blueprints built on a C++ class.
- `tests/test_blueprint_text.py`, a free test of the Blueprint reader, runs on every push.
- `unreal_read_log`: reads the editor's Output Log file: errors and warnings by default, or everything since the last Play In Editor start, with repeats folded and engine network noise hidden. Works with the editor closed (the last session's log).
- `unreal_take_screenshot`: a picture of the level from the editor camera, or of the game view with its UI during Play In Editor, returned as an image. It can look at one actor without moving the user's camera, works with the editor in the background, and keeps nothing on disk.
- `unreal_get_properties` also lists C++ properties that Blueprints and Python can't see by name (protected ones such as `UPROPERTY(EditAnywhere)` members), found from the project's C++ headers.

### Changed
- `programmer` reads the Blueprints built on a C++ class before changing it, so it doesn't break nodes they use or repeat logic they already have.
- `qa` checks Blueprints that use changed C++ and reviews Blueprint logic; `game-designer` reads a feature's Blueprint to see how it behaves now.
- `programmer` and `qa` read the Output Log after the user plays; `programmer`, `qa` and `technical-artist` can look at the level with a screenshot; `art-director` can take its own screenshot to review against the art bible.

### Fixed
- Bridge scripts no longer write Python deprecation warnings into the project's Output Log.

## [0.5.1] - 2026-10-23

### Fixed
- `unreal_get_properties` no longer requires `asset_path`, so reading a placed actor by `actor_label` works.
- The `CLAUDE.md` that `gma-init` writes no longer tells agents to describe editor steps when the editor connection could make the change. It now records whether the connection is on, and `producer` uses that to assign editor tasks.
- `qa`'s read-only rule now states the one exception (the optional build), and `qa` and `game-designer` no longer treat Blueprint-only variables as missing.
- README: the read-only editor tools do ask for permission once; build step wording in the `new-feature` row.

### Changed
- Clearer split between agents: Blueprint values go to `programmer`, sound setup to `audio-director`, store screenshots and capsules to `marketing`; `technical-artist` writes only a "Technical rules" section of the art bible.
- `technical-artist` has the same safety rules as `programmer`.
- `art-director` lists the shared asset prefixes itself; `art-director`, `producer` and `marketing` explain terms for beginners.
- `game-designer` specs can have an "Open questions" section, and new specs are added to the GDD's Features table.

## [0.5.0] - 2026-10-12

### Added
- Unreal Editor connection (Windows): an MCP server that runs on the Python inside Unreal Engine and talks to the open editor through Epic's remote execution, with nothing extra to install. Tools: `unreal_status`, `unreal_list_assets`, `unreal_list_level_actors`, `unreal_get_properties` (read-only) and `unreal_run_python` (asks before every script).
- `gma-init` offers to turn the connection on (Python Editor Script Plugin and "Enable Remote Execution").
- `programmer` and `technical-artist` can change Blueprint values, assets and the level through the editor; `qa` and `game-designer` can read the real values.
- Free tests for the bridge, run on every push.

### Changed
- The safety guard always asks before a Python script runs in the editor, in every folder.
- `technical-artist` audits use real asset types from the editor when it's connected.
- `marketing` no longer writes a feature into store texts just because the user asked, when the design documents say the game doesn't have it (found by the eval suite).
- `gma-init` still writes `CLAUDE.md` when it can't find the engine folder, and asks for the path at the end.

### Fixed
- `technical-artist` wrongly said the Python Editor Script Plugin is on by default; in UE 5.7 it is off.

## [0.4.0] - 2026-10-12

### Added
- Safety guard hook. Inside an Unreal project it blocks text edits to `.uasset` and `.umap` files and to the Unreal Engine installation, and always asks before shell commands that delete or discard files.
- Automated behavior tests (eval suite) for every agent and for `gma-init`, run on a fake Unreal project. See [TESTING.md](TESTING.md).
- GitHub Actions check that validates the plugin and tests the safety guard on every push.

### Changed
- `technical-artist` accepts both `Lvl_` and `L_` as map prefixes instead of flagging `L_`.

## [0.3.0] - 2026-10-10

### Added
- `art-director`: visual style guide, asset list, briefs and prompts for artists or image tools.
- `technical-artist`: naming, folder structure, budgets, materials, read-only Content audits, editor and Blender scripts.
- `audio-director`: sound and music list, audio briefs, Unreal audio setup.
- `marketing`: store page, trailer plan, devlogs, press kit and launch plan; only claims features that exist.

## [0.2.1] - 2026-10-10

### Changed
- Claude runs the Unreal build itself (with the editor closed) instead of sending beginners to Visual Studio. `gma-init` writes the build command into `CLAUDE.md`.
- `programmer` changes existing files in small edits only, and no longer copies Epic's copyright header into new files.

## [0.2.0] - 2026-10-10

### Added
- `game-designer`, `qa` (read-only reviewer) and `producer` agents.
- `/game-maker-agent:new-feature` workflow: spec, code, build, review, editor test, task list.
- `gma-init` creates `Docs/GDD.md`, `Docs/Tasks.md` and offers Unreal-ready `.gitignore` and `.gitattributes` (Git LFS) files.

## [0.1.0] - 2026-10-10

### Added
- First release: plugin marketplace, `programmer` agent and `/game-maker-agent:gma-init`.

[0.5.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.5.0
[0.4.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.4.0
[0.3.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.3.0
[0.2.1]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.2.1
[0.2.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.2.0
[0.1.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.1.0
