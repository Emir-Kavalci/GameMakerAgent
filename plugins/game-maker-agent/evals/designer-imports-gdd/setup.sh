bash "$(dirname "$0")/../_fixtures/unreal-project.sh"

# The user brings their own design document; the project has no GDD yet.
rm -f Docs/GDD.md

cat > MyDesign.md <<'MD'
# Skyhop - my design

Skyhop is a cozy single-player 3D platformer for PC. You play Puff, a small cloud who hops between floating islands to collect lost coins.

## How you play
Each island is a small level. Puff runs, jumps and has a double jump. Collect the coins on the island, then fly through the wind gate to reach the next island.

## Levels
Three islands: Meadow Isle, Crystal Caves, Storm Peak. About one hour in total.

## Extra
On Storm Peak a friend can join on the same PC and play as a second cloud.

## Look and sound
Soft pastel colors, low-poly shapes, calm acoustic guitar music.
MD
