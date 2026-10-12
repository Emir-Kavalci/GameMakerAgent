---
type: llm
---

The Content folder has these badly named assets: Meshes/gem_mesh (should be SM_Gem), Meshes/Rock01 (missing SM_ prefix), Materials/Material_Ground (should be M_Ground), Blueprints/coinPickup_old (missing BP_ prefix). BP_Coin, BP_WindGate, SM_Island_Small, M_Grass, MI_Grass_Dark and L_Meadow already use correct prefixes.
PASS if the reply reports at least three of the four badly named assets with a suggested correct name, and does not say that any of the correctly prefixed assets has a wrong or missing prefix. Optional low-priority style or consistency suggestions about correct names are fine.
FAIL if it misses two or more of the bad names, says a correctly prefixed asset has a wrong or missing prefix, or says it renamed or changed files.
