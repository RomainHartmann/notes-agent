# Project instructions

## Language

- Always communicate in French with the user
- Code, comments, commits, docs, README: all in English
- No comments in the code
- One file = one responsibility

## Git

- Commits: `type(scope): description` (e.g. `feat(auth): add JWT refresh`)
- Types: feat, fix, refactor, test, chore, docs
- One commit per logical change, not per file
- When the user validates a feature ("ok", "c'est bon", "valide", "push", "ship it"), run `git add . && git commit && git push` immediately without asking
- Never leave uncommitted work after validation
- Never discard/revert code (git checkout, git reset, etc.) without asking

## Co-Authored-By

- Add `Co-Authored-By: Claude <noreply@anthropic.com>` only when Claude genuinely contributed to the code (logic, architecture, implementation)
- Do not add it on trivial commits (variable rename, formatting, file move)

## Permissions

- Never read config.json - it contains personal credentials and paths

## Known Gotchas

- [2026-03-25] Claude Code does not always have permissions for git commands. Git operations (checkout, branch, commit, merge) are hardcoded in the shell wrapper script, not delegated to Claude Code.
- [2026-03-25] The launchd PATH is limited (/usr/bin:/bin:/usr/sbin:/sbin). If `claude` is not found, use `claude_path` in config.json with the absolute path.
- [2026-03-25] Apple Notes body is HTML. Responses written to notes must use `<br>` for line breaks, not `\n`.
- [2026-03-25] `claude -p` wraps JSON responses in markdown fences (` ```json ... ``` `) even when told not to. Always strip fences before parsing.
- [2026-03-25] AppleScript `write` uses Mac Roman encoding by default. Always read temp files with `encoding="mac_roman"` in Python.
- [2026-03-25] Claude Code runs with `--dangerously-skip-permissions` for unattended operation. The CLAUDE.md in each target repo is the only guardrail.

## Lessons Learned

- [2026-03-25] No direct Claude API in this project. Everything goes through Claude Code CLI (`claude -p` for analysis, `claude` interactive for tasks). Never add HTTP calls to api.anthropic.com.
