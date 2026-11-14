---
type: regex
target: { source: file, path: Docs/Tasks.md }
pattern: '- \[ \] (Find|Search|Look for|Download|Check (the )?licen|Import)[^\n]*owner: (art-director|audio-director|technical-artist)'
flags: i
match: not_contains
---
