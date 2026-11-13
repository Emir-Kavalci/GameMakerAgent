bash "$(dirname "$0")/../_fixtures/unreal-project.sh"
# The guide was started earlier and stopped before the first feature.
cat > Docs/GettingStarted.md <<'MD'
# Getting started with GameMakerAgent

- [x] 1. Computer check
- [x] 2. Unreal project
- [x] 3. Project setup (/game-maker-agent:gma-init)
- [x] 4. Meet the team
- [ ] 5. First feature (/game-maker-agent:new-feature)
- [ ] 6. Save your work (git commit)

Next step: choose and build a first small feature.
Notes: Git LFS was not installed at the computer check.
MD
