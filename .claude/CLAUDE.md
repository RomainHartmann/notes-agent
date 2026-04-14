# Notes Agent

iPhone note → Claude Code → auto-implemented feature.

## Commands

```
python -m watcher             # Single poll iteration (launchd runs every 60s)
chmod +x install.sh && ./install.sh  # Install launchd agent
```

## Architecture

```
watcher/
├── __main__.py      # Entry point, main loop, debounce logic
├── analysis.py      # Claude CLI prompts (analysis, reflection, rodin)
├── tasks.py         # Shell script generation, worktree execution
├── notes.py         # AppleScript bridge to Apple Notes
├── notifications.py # Pushover push notifications
├── state.py         # Content hashing for change detection
└── config.py        # Config loading, logging
```

## Stack

- Python 3 (stdlib only, zero pip dependencies)
- macOS: AppleScript + launchd + Terminal.app
- Claude Code CLI (`claude -p` for analysis, `claude` interactive for tasks)
- Git worktrees for parallel isolated execution
- Pushover for mobile notifications

## Key Design Decisions

- No direct Claude API calls — everything goes through Claude Code CLI
- One file = one responsibility
- No comments in the code
- Apple Notes body is HTML — responses use `<br>`, not `\n`
- Autonomous mode: `--dangerously-skip-permissions` with CLAUDE.md as the only guardrail

## Language

- Communicate with user in French
- Code, commits, docs, README: English

## Git

- Commits: `type(scope): description` (e.g. `feat(tasks): add PR mode`)
- Types: feat, fix, refactor, test, chore, docs
- One commit per logical change
- When user validates ("ok", "c'est bon", "push", "ship it") → commit and push immediately
- Never discard/revert code without asking
- Co-Authored-By: Claude <noreply@anthropic.com> only on genuine contributions
