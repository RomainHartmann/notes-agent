---
paths:
  - "watcher/**/*.py"
---
# Python Code Style

- Python 3 stdlib only — never add pip dependencies
- No comments unless logic is truly non-obvious
- No type annotations on internal helpers
- One file = one responsibility — split before a module grows past ~150 lines
- Prefer editing existing files over creating new ones
- Use `subprocess.run` with `capture_output=True, text=True` for shell commands
- Always set `timeout` on subprocess calls to prevent hangs
- Encoding: read temp files from AppleScript with `encoding="mac_roman"`
- f-strings over `.format()` or `%`
- Flat is better than nested — avoid deep callback chains
