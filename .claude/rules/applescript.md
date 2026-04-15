---
paths:
  - "watcher/notes.py"
  - "watcher/tasks.py"
---
# AppleScript Integration Rules

- Apple Notes body is HTML — use `<br>` for line breaks, never `\n`
- AppleScript `write` uses Mac Roman encoding — always read temp files with `encoding="mac_roman"`
- Tag injection: insert tags as `<div>#tag</div>` after the first `</div>` in the note body
- Note IDs contain `/`, `:`, and spaces — always sanitize before using in file paths
- Use `run_applescript()` from `watcher.notes` — never call `osascript` directly from other modules
- Terminal.app is launched via AppleScript `do script` for interactive Claude sessions
- AppleScript strings: escape `\` and `"` before embedding in scripts
- HTML entity escaping: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;` before writing to notes
