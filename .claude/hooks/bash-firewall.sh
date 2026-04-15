#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

BLOCKED_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf \$HOME"
    "git push --force main"
    "git push --force master"
    "git push -f origin main"
    "git push -f origin master"
    "git reset --hard"
    "cat config.json"
    "less config.json"
    "head config.json"
    "tail config.json"
    "> config.json"
    "curl.*pushover"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
        echo "BLOCKED by bash-firewall: matches '$pattern'" >&2
        exit 2
    fi
done

exit 0
