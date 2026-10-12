# Changelog

All notable changes to GameMakerAgent are listed here. Versions follow [Semantic Versioning](https://semver.org/); while the version starts with `0.`, any release may change how agents behave.

To update an installed copy, run `/plugin marketplace update game-maker-agent` in Claude Code, then `/plugin update game-maker-agent@game-maker-agent`, and restart Claude Code.

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

[0.4.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.4.0
[0.3.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.3.0
[0.2.1]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.2.1
[0.2.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.2.0
[0.1.0]: https://github.com/Emir-Kavalci/GameMakerAgent/releases/tag/game-maker-agent--v0.1.0
