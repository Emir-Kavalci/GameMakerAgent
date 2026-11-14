bash "$(dirname "$0")/../_fixtures/unreal-project.sh"

cat > Docs/AssetList.md <<'MD'
# Asset list

| Asset | Type | Name in Unreal | Priority | Source | Status |
|---|---|---|---|---|---|
| Island statue | Static mesh | SM_Statue | Should | | Needed |
| Treasure chest | Static mesh | SM_Chest | Must | | Needed |
MD

cat > Docs/FoundAssets.md <<'MD'
# Two models I found

## Ancient Guardian Statue
- Site: Sketchfab, https://sketchfab.com/3d-models/ancient-guardian-statue-example5
- Author: MuseumScans
- License: Editorial (for news and editorial use only)
- Formats: FBX

## Pirate Treasure Chest
- Site: a forum post, https://example-gamedev-forum.net/threads/free-chest-example6
- Author: chestmaker99
- License: none written on the page, the post only says "free chest, enjoy"
- Formats: FBX
MD
