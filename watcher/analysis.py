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
    '- "needs_code": true if answering accurately requires reading the codebase '
    "(e.g. checking a model, a config, a limit, a behavior). false otherwise.\n"
    '- "target": (only when needs_code is true) "frontend" or "backend" — '
    "which codebase to inspect. Use the same deduction rules as for tasks.\n"
    '- "response": (only when needs_code is false) structured answer in the same '
    "language as the note. Be concrete, give pros/cons or recommendations if relevant. "
    "Plain text, no markdown.\n"
    '- "needs_rodin": true if the question touches product design, UX, feature scope, '
    "limits, architecture decisions, or anything where a critical/devil's advocate "
    "perspective would add value. false for purely technical or factual questions.\n"
    '- "pushover_summary": single short sentence (max 100 chars) summarizing the '
    "response or the question being investigated\n\n"
    'If the note is too vague or ambiguous to act on, return a single item of type "clarification":\n'
    '- "type": "clarification"\n'
    '- "questions": specific questions to ask the user, in the same language as the note. Plain text.\n'
    '- "pushover_summary": single short sentence (max 100 chars) summarizing what is unclear\n\n'
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


CODE_REFLECTION_PROMPT = (
    "You are answering a developer's question about this codebase. "
    "You have full read access to the project.\n\n"
    "Rules:\n"
    "- Start with the direct answer (yes/no, the value, the limit, etc.)\n"
    "- Then give a brief explanation with evidence from the code (file, model, config)\n"
    "- Same language as the question\n"
    "- Plain text only, no markdown\n"
    "- Be concise: 2-4 sentences max\n\n"
    "Question: {question}"
)


def reflect_with_code(title, body, project_path, claude_path, claude_model=None):
    question = f"{title}\n{body}" if body else title
    prompt = CODE_REFLECTION_PROMPT.format(question=question)
    cmd = [claude_path, "-p", prompt, "--output-format", "json"]
    if claude_model:
        cmd.extend(["--model", claude_model])
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=120,
        cwd=project_path
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    envelope = json.loads(result.stdout)
    return strip_markdown_fences(envelope["result"])


RODIN_PROMPT = (
    "You are Rodin, a Socratic product advisor. You receive a developer's question "
    "and the factual answer extracted from the codebase.\n\n"
    "Your role:\n"
    "- Challenge the status quo: is the current behavior actually a good idea?\n"
    "- Think from the end-user perspective: what are the UX consequences?\n"
    "- Raise edge cases, scalability issues, or design blind spots\n"
    "- Suggest concrete improvements if relevant\n"
    "- Be direct and opinionated, not neutral\n\n"
    "Rules:\n"
    "- Same language as the question\n"
    "- Plain text only, no markdown\n"
    "- Be concise: 3-5 sentences max\n"
    "- Start with your verdict (is this a problem or not?)\n\n"
    "Question: {question}\n\n"
    "Factual answer: {answer}"
)


def rodin_reflect(question, factual_answer, claude_path, claude_model=None):
    prompt = RODIN_PROMPT.format(question=question, answer=factual_answer)
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
    return strip_markdown_fences(envelope["result"])


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
