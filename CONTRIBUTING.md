# Contributing to GameMakerAgent

Thanks for helping. GameMakerAgent is a free, open-source plugin for solo Unreal Engine developers, and most of it is plain-text instructions, so you don't need to be a programmer to improve it.

## Ways to help

- **Report a problem.** If an agent did something wrong, open an issue with the "Agent did the wrong thing" form. Say what you asked, what the agent did, and what you expected. This is the most useful kind of report.
- **Suggest an idea.** Use the "Feature idea" form for a new agent, workflow or improvement.
- **Change the plugin.** Fix an agent's instructions, add a test case, or improve the docs with a pull request.

Please be kind and constructive in issues and pull requests.

## How the repository is organized

```
.claude-plugin/marketplace.json     the marketplace Claude Code installs from
plugins/game-maker-agent/
  .claude-plugin/plugin.json        plugin name and version
  agents/<role>.md                  one file per agent: frontmatter + instructions
  skills/<name>/SKILL.md            slash commands (gma-init, new-feature)
  hooks/                            the safety guard
  mcp/                              the Unreal Editor bridge (MCP server)
  evals/                            behavior tests (see TESTING.md)
tests/                              free tests for the safety guard and the bridge
```

## Making a change

1. Fork the repository and create a branch.
2. Install your copy instead of the published one, so you can try your change in a real Unreal project:
   ```
   claude --plugin-dir path/to/your/fork/plugins/game-maker-agent
   ```
3. Make the change. Keep it small and focused on one problem.
4. Run the free checks (see [TESTING.md](TESTING.md)):
   ```bash
   claude plugin validate .
   claude plugin validate plugins/game-maker-agent
   bash tests/test-guard.sh
   python tests/test_bridge.py
   ```
5. If you changed an agent or skill, run its eval case if you can. This uses your own Claude plan, so it's optional; say in the pull request whether you ran it.
6. Open a pull request and fill in the template.

## Guidelines for agent and skill instructions

- **Write for beginners.** Users are often new to Unreal Engine. Agents should explain terms and give click-by-click editor steps.
- **One role per agent.** The agent that writes code never reviews it; `qa` stays read-only.
- **Be honest about limits.** Agents never claim to have made images, audio or features that don't exist.
- **Safe by default.** Agents never edit `.uasset`/`.umap` files or engine files, and ask before deleting anything.
- **Portable.** Use relative paths and `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}`; never hard-code a path from your own machine.
- **Free.** Don't add anything that needs a paid service, an API key, or model calls that run automatically.
- **Plain English** in plugin files; agents reply in the user's language on their own.
- When a change alters what users see, add a line to [CHANGELOG.md](CHANGELOG.md) under a new "Unreleased" heading.

## Releasing (maintainer)

1. Bump `version` in `plugins/game-maker-agent/.claude-plugin/plugin.json`, `SERVER_VERSION` in `plugins/game-maker-agent/mcp/unreal_bridge.py` and the status line in `README.md`.
2. Move the "Unreleased" changelog entries under the new version and date.
3. Commit, push, and tag with `claude plugin tag plugins/game-maker-agent --push`.
4. Create a GitHub release from the tag, using the changelog entry as the description.

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).
