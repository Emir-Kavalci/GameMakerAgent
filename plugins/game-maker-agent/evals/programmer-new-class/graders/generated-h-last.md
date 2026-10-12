---
type: regex
target: { source: file, path: Source/Skyhop/Checkpoint.h }
pattern: 'Checkpoint\.generated\.h"[^]*#include'
match: not_contains
---
