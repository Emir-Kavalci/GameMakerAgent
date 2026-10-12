# Security

GameMakerAgent runs inside Claude Code on your computer. Its agents can read and write files in your project, and its safety guard hook runs before file edits and shell commands.

## Reporting a problem

If you find a way the plugin could damage a user's project or computer, such as a way around the safety guard or an agent instruction that leads to deleting or leaking files, please **don't open a public issue**. Report it privately instead:

1. Open the repository's **Security** tab on GitHub.
2. Click **Report a vulnerability** and describe the problem and how to reproduce it.

You'll get an answer as soon as possible. This is a volunteer project, so there is no bug bounty.

## Supported versions

Only the latest release gets fixes. Update with `/plugin update game-maker-agent@game-maker-agent`.

## What the safety guard is and isn't

The guard catches common mistakes (editing binary assets, changing engine files, deleting files without asking). It is a safety net, not a security boundary, and it doesn't replace Claude Code's own permission prompts or your backups. Keep your project in git.
