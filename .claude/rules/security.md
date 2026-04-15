# Security Rules

- NEVER read `config.json` — it contains personal credentials (Pushover tokens, paths)
- NEVER hardcode API tokens, keys, or secrets in source code
- Pushover tokens flow through config → function params — never import config in notifications.py
- The `--dangerously-skip-permissions` flag is used for unattended operation — the CLAUDE.md in each target repo is the only guardrail
- Shell scripts generated in `/tmp/` contain credentials (Pushover tokens) — they are auto-deleted after execution
- Note IDs from AppleScript are untrusted input — sanitize before using in file paths or shell commands
- AppleScript string injection: always escape `"` and `\` in user-provided content before embedding in scripts
