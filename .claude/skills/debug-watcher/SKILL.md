---
name: debug-watcher
description: >
  Debug the watcher pipeline. Use when a note isn't being processed, Claude analysis
  fails, tasks don't launch, or notifications aren't sent.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

You are debugging the notes-agent watcher pipeline.

## Diagnostic steps

1. **Check logs** — Read `watcher.log` for recent errors (skip credential lines)
2. **Check state** — Read `state.json` for stuck pending notes
3. **Trace the pipeline** — Follow the flow: notes.py → analysis.py → __main__.py → tasks.py
4. **Common failures**:
   - Note not picked up → check tags in note body (`#claude-done`, `#claude-exists`, `#claude-pending`)
   - Analysis fails → Claude CLI path wrong, model not available, JSON parse error (markdown fences)
   - Task doesn't launch → Terminal.app permissions, worktree conflicts, branch collision
   - Notification fails → Pushover tokens invalid, network timeout
5. **Verify config** — Check config.example.json for expected fields (never read config.json directly)

## Rules

- Report in French
- Show the exact error and the fix
- Never read config.json (credentials)
