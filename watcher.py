#!/usr/bin/env python3

import subprocess
import json
import os
import urllib.request
import urllib.parse
import tempfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_PATH = os.path.join(BASE_DIR, "watcher.log")


def log(message):
    with open(LOG_PATH, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def run_applescript(script):
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def get_unprocessed_note_ids(folder, done_tag, exists_tag):
    script = f'''tell application "Notes"
    set idList to ""
    try
        set targetFolder to first folder whose name is "{folder}"
        repeat with aNote in notes of targetFolder
            set b to body of aNote
            if b does not contain "#{done_tag}" and b does not contain "#{exists_tag}" then
                set idList to idList & (id of aNote) & linefeed
            end if
        end repeat
    end try
    return idList
end tell'''
    output, _ = run_applescript(script)
    return [line.strip() for line in output.split("\n") if line.strip()]


def get_note_content(note_id):
    safe_id = note_id.replace("/", "_").replace(":", "_").replace(" ", "_")
    tmp_path = os.path.join(tempfile.gettempdir(), f"note_{safe_id}.txt")
    script = f'''tell application "Notes"
    set aNote to note id "{note_id}"
    set fileRef to open for access POSIX file "{tmp_path}" with write permission
    set eof of fileRef to 0
    write (name of aNote) & linefeed & "---SEP---" & linefeed & (body of aNote) to fileRef
    close access fileRef
end tell'''
    _, code = run_applescript(script)
    if code != 0 or not os.path.exists(tmp_path):
        return None, None
    with open(tmp_path) as f:
        content = f.read()
    os.remove(tmp_path)
    parts = content.split("\n---SEP---\n", 1)
    title = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    return title, body


def analyze_with_claude(title, body, claude_path):
    prompt = (
        "Analyze this developer note. Return ONLY a valid JSON object, "
        "no markdown, no backticks, no explanation.\n\n"
        "A note can contain multiple independent items. Return a JSON object with "
        'an "items" array. Each item is either a "task" (something to implement, '
        'fix, debug, refactor in the codebase) or a "reflection" (an idea, question, '
        "architectural thinking, opinion request, or anything that does not require "
        "touching code right now).\n\n"
        "When ambiguous, pick the dominant type.\n\n"
        'For each item of type "task":\n'
        '- "type": "task"\n'
        '- "target": "frontend" or "backend"\n'
        '- "branch_name": kebab-case branch name prefixed with feat/, fix/, or chore/\n'
        '- "task_description": complete task description in the same language as the note\n\n'
        'For each item of type "reflection":\n'
        '- "type": "reflection"\n'
        '- "response": structured answer in the same language as the note. Be concrete, '
        "give pros/cons or recommendations if relevant. Plain text, no markdown.\n"
        '- "pushover_summary": single short sentence (max 100 chars) summarizing the response\n\n'
        "Deduction rules for target when type is task:\n"
        "- frontend: UI, component, style, Flutter, widget, screen, page, display, layout, animation\n"
        "- backend: API, database, server, route, endpoint, model, auth, query, migration, cron\n\n"
        f"Note title: {title}\n"
        f"Note content:\n"
        f"{body if body else '(empty body, infer from title only)'}"
    )
    result = subprocess.run(
        [claude_path, "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, timeout=120,
        cwd=tempfile.gettempdir()
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    envelope = json.loads(result.stdout)
    return json.loads(envelope["result"])


def write_response_to_note(note_id, response_text):
    html_response = (response_text
                     .replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;")
                     .replace("\n", "<br>"))
    safe_html = html_response.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''tell application "Notes"
    set aNote to note id "{note_id}"
    set body of aNote to (body of aNote) & "<br><br>---<br>" & "{safe_html}"
end tell'''
    run_applescript(script)


def send_pushover(title, message, config):
    payload = urllib.parse.urlencode({
        "token": config["pushover_app_token"],
        "user": config["pushover_user_key"],
        "title": title,
        "message": message
    }).encode()
    req = urllib.request.Request(
        "https://api.pushover.net/1/messages.json",
        data=payload
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        log(f"Pushover error: {e}")


def build_replace_tag_command(note_id, done_tag, exists_tag):
    return (
        f'osascript '
        f'-e \'tell application "Notes"\' '
        f'-e \'set aNote to note id "{note_id}"\' '
        f'-e \'set b to body of aNote\' '
        f'-e \'set body of aNote to do shell script "echo " '
        f'& quoted form of b & " | sed s/#{done_tag}/#{exists_tag}/g"\' '
        f'-e \'end tell\''
    )


def build_task_prompt(item):
    return (
        "Analyze the project and implement the requested feature.\n\n"
        "If the feature or fix already exists in the code with no changes needed:\n"
        "- Do not modify any project files.\n"
        "- Create a file named .claude_feature_exists at the project root.\n"
        "- Briefly explain what you found.\n\n"
        "If it does not exist yet:\n"
        "- Implement the necessary changes.\n"
        "- Do not run any git operations (no commit, no push, no checkout).\n\n"
        f"Request: {item['task_description']}"
    )


def launch_claude_code(project_path, task_prompt, note_id, item, config):
    safe_id = note_id.replace("/", "_").replace(":", "_").replace(" ", "_")
    task_path = os.path.join(tempfile.gettempdir(), f"claude_task_{safe_id}.txt")
    runner_path = os.path.join(tempfile.gettempdir(), f"run_claude_{safe_id}.sh")
    claude_path = config.get("claude_path", "claude")
    dev_branch = config["dev_branch"]
    branch = item["branch_name"]
    done_tag = config["processed_tag"]
    exists_tag = config["exists_tag"]
    replace_cmd = build_replace_tag_command(note_id, done_tag, exists_tag)

    commit_prefix = branch.split("/")[0] if "/" in branch else "feat"
    commit_desc = branch.split("/", 1)[1].replace("-", " ") if "/" in branch else branch
    safe_commit_msg = f"{commit_prefix}: {commit_desc}".replace('"', '\\"')

    with open(task_path, "w") as f:
        f.write(task_prompt)

    with open(runner_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f'cd "{project_path}"\n\n')
        f.write(f"git checkout {dev_branch} && git pull origin {dev_branch}\n")
        f.write(f"git checkout -b {branch}\n\n")
        f.write(f'TASK=$(cat "{task_path}")\n')
        f.write(f'{claude_path} "$TASK"\n\n')
        f.write('if [ -f ".claude_feature_exists" ]; then\n')
        f.write('    rm -f ".claude_feature_exists"\n')
        f.write(f"    git checkout {dev_branch}\n")
        f.write(f"    git branch -d {branch}\n")
        f.write(f"    {replace_cmd}\n")
        f.write("else\n")
        f.write("    git add -A\n")
        f.write(f'    git commit -m "{safe_commit_msg}"\n')
        f.write(f"    git checkout {dev_branch} && git merge {branch}\n")
        f.write("fi\n\n")
        f.write(f'rm -f "{task_path}" "{runner_path}"\n')

    os.chmod(runner_path, 0o755)

    script = f'''tell application "Terminal"
    activate
    do script "bash \\"{runner_path}\\""
end tell'''
    run_applescript(script)


def tag_note(note_id, tag):
    script = f'''tell application "Notes"
    set aNote to note id "{note_id}"
    set body of aNote to (body of aNote) & " #{tag}"
end tell'''
    run_applescript(script)


def process_item(item, note_id, title, config):
    done_tag = config["processed_tag"]

    if item["type"] == "reflection":
        write_response_to_note(note_id, item["response"])
        send_pushover(f"\U0001f4a1 {title}", item["pushover_summary"], config)
        tag_note(note_id, done_tag)
        log(f"Reflection answered: '{title}'")

    elif item["type"] == "task":
        tag_note(note_id, done_tag)
        task_prompt = build_task_prompt(item)
        project_path = config["frontend_path"] if item["target"] == "frontend" else config["backend_path"]
        launch_claude_code(project_path, task_prompt, note_id, item, config)
        send_pushover(
            f"\U0001f6e0 Task launched: {title}",
            f"{item['target'].capitalize()} - {item['branch_name']}",
            config
        )
        log(f"Task launched: '{title}' -> {item['target']} / {item['branch_name']}")


def main():
    try:
        config = load_config()
    except Exception as e:
        log(f"Config error: {e}")
        return

    folder = config["notes_folder"]
    done_tag = config["processed_tag"]
    exists_tag = config["exists_tag"]
    claude_path = config.get("claude_path", "claude")

    note_ids = get_unprocessed_note_ids(folder, done_tag, exists_tag)
    if not note_ids:
        return

    for note_id in note_ids:
        title, body = get_note_content(note_id)
        if title is None:
            log(f"Unreadable note: {note_id}")
            continue
        if not title and not body:
            log(f"Empty note skipped: {note_id}")
            continue

        try:
            analysis = analyze_with_claude(title, body, claude_path)
        except Exception as e:
            log(f"Claude analysis error for '{title}': {e}")
            continue

        items = analysis.get("items", [])
        if not items:
            log(f"No items in analysis for '{title}'")
            continue

        for item in items:
            process_item(item, note_id, title, config)


if __name__ == "__main__":
    main()
