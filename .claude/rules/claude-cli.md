---
paths:
  - "watcher/analysis.py"
---
# Claude Code CLI Gotchas

- No direct Claude API calls (api.anthropic.com) — everything goes through `claude -p` or `claude` interactive
- `claude -p` wraps JSON responses in markdown fences (` ```json ... ``` `) even when told not to — always strip fences before parsing via `strip_markdown_fences()`
- Use `--output-format json` with `-p` mode — response is in `envelope["result"]`
- Claude Code in `-p` mode may refuse destructive Bash commands (like `rm`) even with `--dangerously-skip-permissions` — file creation/editing works fine, deletion is unreliable
- The launchd PATH is limited (`/usr/bin:/bin:/usr/sbin:/sbin`) — use `claude_path` from config.json with the absolute path
- Always run `claude -p` with a `cwd` parameter pointing to the relevant project for codebase-aware answers
- Rodin (Socratic advisor) runs in `tempfile.gettempdir()` as cwd since it doesn't need codebase access
