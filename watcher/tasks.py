import os
import tempfile

from watcher.notes import run_applescript, build_replace_tag_command

DEFAULT_CLAUDE_MD = """\
# Project rules

## Safety

- Only delete or overwrite files if the task explicitly requires it
- Never run any git operations (no commit, no push, no checkout, no branch)
- Keep changes minimal and focused on the requested task
- Do not modify files unrelated to the task

## Code style

- No comments unless the logic is non-obvious
- Prefer editing existing files over creating new ones
"""

TASK_PROMPT = (
    "Analyze the project and implement the requested feature.\n\n"
    "You are running in fully autonomous mode. All permissions are granted. "
    "Do not ask for confirmation. Execute all necessary commands directly, "
    "including file deletion if the task requires it.\n\n"
    "If the feature or fix already exists in the code with no changes needed:\n"
    "- Do not modify any project files.\n"
    "- Create a file named .claude_feature_exists at the project root.\n"
    "- Briefly explain what you found.\n\n"
    "If it does not exist yet:\n"
    "- Implement the necessary changes.\n"
    "- Do not run any git operations (no commit, no push, no checkout).\n\n"
    "Request: {task_description}"
)


def build_task_prompt(item):
    return TASK_PROMPT.format(task_description=item["task_description"])


def launch_claude_code(project_path, task_prompt, note_id, item, config, title=""):
    safe_id = note_id.replace("/", "_").replace(":", "_").replace(" ", "_")
    branch_id = item["branch_name"].replace("/", "_")
    task_path = os.path.join(tempfile.gettempdir(), f"claude_task_{safe_id}_{branch_id}.txt")
    runner_path = os.path.join(tempfile.gettempdir(), f"run_claude_{safe_id}_{branch_id}.sh")
    claude_path = config.get("claude_path", "claude")
    dev_branch = config["dev_branch"]
    branch = item["branch_name"]
    replace_cmd = build_replace_tag_command(
        note_id, config["processed_tag"], config["exists_tag"]
    )

    commit_prefix = branch.split("/")[0] if "/" in branch else "feat"
    commit_desc = branch.split("/", 1)[1].replace("-", " ") if "/" in branch else branch
    safe_commit_msg = f"{commit_prefix}: {commit_desc}".replace('"', '\\"')

    with open(task_path, "w") as f:
        f.write(task_prompt)

    worktree_dir = os.path.join(tempfile.gettempdir(), f"claude_worktree_{branch_id}")

    with open(runner_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f'REPO="{project_path}"\n')
        f.write(f'WORKTREE="{worktree_dir}"\n\n')
        f.write(f'cd "$REPO"\n')
        f.write(f"git checkout {dev_branch} 2>/dev/null || git checkout -b {dev_branch}\n")
        f.write(f"git pull origin {dev_branch} 2>/dev/null || true\n")
        f.write('git log -1 >/dev/null 2>&1 || git commit --allow-empty -m "init"\n\n')
        f.write(f'BRANCH="{branch}"\n')
        f.write('N=2\n')
        f.write('while git show-ref --verify --quiet "refs/heads/$BRANCH"; do\n')
        f.write(f'    BRANCH="{branch}-$N"\n')
        f.write('    N=$((N+1))\n')
        f.write('done\n\n')
        f.write('rm -rf "$WORKTREE"\n')
        f.write('git worktree add "$WORKTREE" -b "$BRANCH"\n')
        f.write('cd "$WORKTREE"\n\n')
        f.write('if [ ! -f ".gitignore" ]; then\n')
        f.write('    echo ".DS_Store" > .gitignore\n')
        f.write('fi\n')
        f.write('grep -qx ".DS_Store" .gitignore 2>/dev/null || echo ".DS_Store" >> .gitignore\n\n')
        f.write('if [ ! -f ".claude/CLAUDE.md" ] && [ ! -f "CLAUDE.md" ]; then\n')
        f.write('    mkdir -p .claude\n')
        f.write(f'    cat > .claude/CLAUDE.md << \'CLAUDEMD\'\n{DEFAULT_CLAUDE_MD}CLAUDEMD\n')
        f.write('fi\n\n')
        f.write(f'TASK=$(cat "{task_path}")\n')
        claude_model = config.get("claude_model", "")
        model_flag = f' --model "{claude_model}"' if claude_model else ""
        f.write(f'caffeinate -s {claude_path} -p --dangerously-skip-permissions{model_flag} "$TASK"\n\n')
        pushover_token = config.get("pushover_app_token", "")
        pushover_user = config.get("pushover_user_key", "")
        safe_title = title.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        target = item["target"].capitalize()

        f.write('if [ -f ".claude_feature_exists" ]; then\n')
        f.write('    rm -f ".claude_feature_exists"\n')
        f.write('    cd "$REPO"\n')
        f.write('    git worktree remove "$WORKTREE" --force\n')
        f.write('    git branch -d "$BRANCH"\n')
        f.write(f"    {replace_cmd}\n")
        f.write(f'    curl -s -F "token={pushover_token}" -F "user={pushover_user}" '
                f'-F "title=Feature already exists: {safe_title}" '
                f'-F "message={target} - $BRANCH" '
                f'https://api.pushover.net/1/messages.json > /dev/null\n')
        f.write("else\n")
        f.write("    git add -A\n")
        f.write(f'    git commit -m "{safe_commit_msg}"\n')
        f.write('    cd "$REPO"\n')
        f.write(f"    git checkout {dev_branch}\n")
        f.write(f'    git pull --rebase origin {dev_branch} 2>/dev/null || true\n')
        f.write(f'    git merge "$BRANCH"\n')
        f.write(f'    git push -u origin {dev_branch}\n')
        f.write('    git worktree remove "$WORKTREE" --force\n')
        f.write('    git branch -d "$BRANCH"\n')
        f.write(f'    curl -s -F "token={pushover_token}" -F "user={pushover_user}" '
                f'-F "title=Task done: {safe_title}" '
                f'-F "message={target} - $BRANCH" '
                f'https://api.pushover.net/1/messages.json > /dev/null\n')
        f.write("fi\n\n")
        f.write(f'rm -f "{task_path}" "{runner_path}"\n')

    os.chmod(runner_path, 0o755)

    script = f'''tell application "Terminal"
    activate
    do script "bash \\"{runner_path}\\""
end tell'''
    run_applescript(script)
