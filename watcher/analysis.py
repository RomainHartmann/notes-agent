import json
import subprocess
import tempfile

ANALYSIS_PROMPT = (
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
    "- backend: API, database, server, route, endpoint, model, auth, query, migration, cron"
)


def strip_markdown_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def analyze_with_claude(title, body, claude_path, claude_model=None):
    prompt = (
        f"{ANALYSIS_PROMPT}\n\n"
        f"Note title: {title}\n"
        f"Note content:\n"
        f"{body if body else '(empty body, infer from title only)'}"
    )
    cmd = [claude_path, "-p", prompt, "--output-format", "json"]
    if claude_model:
        cmd.extend(["--model", claude_model])
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=120,
        cwd=tempfile.gettempdir()
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    envelope = json.loads(result.stdout)
    raw = strip_markdown_fences(envelope["result"])
    return json.loads(raw)
