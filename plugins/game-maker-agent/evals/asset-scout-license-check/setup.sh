bash "$(dirname "$0")/../_fixtures/unreal-project.sh"

cat > Docs/AssetList.md <<'MD'
# Asset list

| Asset | Type | Name in Unreal | Priority | Source | Status |
|---|---|---|---|---|---|
| Floating island rock | Static mesh | SM_Island_Rock | Must | | Needed |
| Wind gate arch | Static mesh | SM_WindGate | Must | | Needed |
MD

cat > Docs/FoundAssets.md <<'MD'
# Two models I found

## Low Poly Floating Island
- Site: Sketchfab, https://sketchfab.com/3d-models/low-poly-floating-island-example1
- Author: SkyCrafter
- License: CC Attribution-NonCommercial (CC BY-NC 4.0)
- Formats: FBX, glTF

## Stone Arch Gate
- Site: OpenGameArt, https://opengameart.org/content/stone-arch-gate-example2
- Author: Mira Holt
- License: CC-BY 4.0
- Formats: FBX
MD
