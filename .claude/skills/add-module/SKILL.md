---
name: add-module
description: >
  Scaffold a new watcher module. Use when adding a new responsibility to the
  watcher (new integration, new processing step, new output channel).
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

You are adding a new module to the notes-agent watcher.

## Architecture rules

- One file = one responsibility → create `watcher/<module_name>.py`
- Zero pip dependencies → stdlib only (subprocess, json, os, tempfile, urllib, hashlib)
- No comments unless logic is non-obvious
- Follow existing patterns:
  - Config flows via function params, never import config.py in leaf modules
  - Logging via `from watcher.config import log`
  - AppleScript via `from watcher.notes import run_applescript`
- Wire the new module into `__main__.py` following the existing import + process_item pattern
- Update CLAUDE.md architecture diagram if adding a new file

## Checklist

1. Create `watcher/<name>.py` with a clean public API
2. Import and integrate in `__main__.py`
3. Update the architecture section in `.claude/CLAUDE.md`
4. Test manually with `python -m watcher`
