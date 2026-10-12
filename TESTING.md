# Testing GameMakerAgent

GameMakerAgent has three kinds of checks. Run them before you publish a change to an agent, a skill or the safety hook.

| Check | What it tests | Cost | Runs on GitHub |
| --- | --- | --- | --- |
| `claude plugin validate` | Manifests and the agent, skill and hook files are well-formed | Free | Yes, on every push |
| `tests/test-guard.sh` | The safety hook blocks and allows the right tool calls | Free | Yes, on every push |
| Eval suite (`claude plugin eval`) | Each agent and skill behaves the way its instructions say | Uses the Claude plan of whoever runs it | No, run it yourself |

GameMakerAgent itself is free. People who install the plugin never run these tests and are never charged for them. The eval suite only runs when a developer of this repository starts it by hand, and then it counts against that developer's own Claude plan. Nothing runs it automatically.

## Validate and hook tests

From the repository root (on Windows, use Git Bash):

```bash
claude plugin validate .
claude plugin validate plugins/game-maker-agent
bash tests/test-guard.sh
```

## Eval suite

The cases live in `plugins/game-maker-agent/evals/`, one folder per case. Each case:

1. builds a small fake Unreal 5.7 C++ project called **Skyhop** with `evals/_fixtures/unreal-project.sh` (no real engine needed),
2. sends one realistic request, such as "Use the qa agent to review SpeedPad.cpp",
3. grades the result with fixed checks (files created or untouched, text patterns) and a few judge-model checks.

| Case | What it proves |
| --- | --- |
| `designer-writes-spec` | game-designer writes a spec with testable acceptance criteria and no code |
| `programmer-new-class` | programmer follows the project's module layout, `_API` macro and Unreal header rules |
| `programmer-refuses-uasset` | `.uasset` files are never edited as text (agent rule and safety hook) |
| `qa-finds-bug-read-only` | qa finds a real crash bug against the spec and changes no files |
| `producer-plans-milestone` | producer writes small tasks with owners and keeps finished work |
| `marketing-no-fake-features` | marketing refuses to advertise a feature the game doesn't have |
| `tech-artist-audit-read-only` | technical-artist finds badly named assets and changes nothing |
| `art-director-no-images` | art-director says it can't make images and offers a brief instead |
| `audio-director-no-audio` | audio-director says it can't make sound files and offers a brief instead |
| `gma-init-sets-up-project` | gma-init writes CLAUDE.md with the right facts, the GDD and the task list |
| `gma-init-outside-project` | gma-init stops when the folder isn't an Unreal project |

The `new-feature` workflow isn't covered: it stops for the user at every checkpoint, so it is tested by hand on a real project.

### Run it

From `plugins/game-maker-agent/`:

```bash
# Quick check: every case once (about 1 USD with Sonnet)
claude plugin eval . --scaffold --trust-plugin --allow-tools Write Edit --ablation none --runs 1 -j 4 --model sonnet

# One case, three runs, after changing one agent
claude plugin eval . --case qa-finds-bug-read-only --scaffold --trust-plugin --allow-tools Write Edit --ablation none -j 3 --model sonnet
```

What the flags mean:

- `--scaffold` runs each case's `setup.sh`, which creates the fake project. Only use it on cases you have read.
- `--allow-tools Write Edit` lets agents write files inside the throwaway test folder. Bash isn't granted, because on native Windows the eval sandbox can't run shell commands, so cases never depend on Bash.
- `--ablation none` skips the "without the plugin" comparison. It is meaningless here, because the agents don't exist without the plugin.

Results go to `evals/results/` (ignored by git). Open the `report.html` there to see every check and the judge's reasons.

A single run is noisy. Before you decide that a change made an agent better or worse, run the affected case three times (the default).
