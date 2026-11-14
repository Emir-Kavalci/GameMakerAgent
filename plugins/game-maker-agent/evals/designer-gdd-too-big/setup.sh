bash "$(dirname "$0")/../_fixtures/unreal-project.sh"
rm -f Docs/GDD.md

cat > MyDesign.md <<'MD'
# Skyrealms Online - my design

I am making this alone in my free time.

Skyrealms Online is an open-world MMORPG for PC and consoles with thousands of players on the same servers.

## World
A seamless open world of 50 floating regions, each with its own towns, dungeons and weather.

## Systems
- Crafting with 400 recipes and a player-driven market
- Guilds with guild halls and guild wars
- Open-world PvP and ranked arenas
- Mounts, pets and housing
- Full voice acting for every character, in 8 languages

## Look
Realistic graphics, as good as the biggest games.
MD
