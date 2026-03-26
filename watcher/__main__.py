import time

from watcher.config import log, load_config
from watcher.notes import get_unprocessed_note_ids, get_note_content, write_response_to_note, tag_note
from watcher.analysis import analyze_with_claude, reflect_with_code, rodin_reflect
from watcher.tasks import build_task_prompt, launch_claude_code
from watcher.notifications import send_pushover
from watcher.state import load_state, save_state, content_hash

PENDING_TAG = "claude-pending"
DEBOUNCE_SECONDS = 15


def process_item(item, note_id, title, body, config):
    done_tag = config["processed_tag"]
    claude_path = config.get("claude_path", "claude")
    claude_model = config.get("claude_model", "")

    if item["type"] == "reflection":
        if item.get("needs_code"):
            project_path = config["frontend_path"] if item["target"] == "frontend" else config["backend_path"]
            response = reflect_with_code(title, body, project_path, claude_path, claude_model)
        else:
            response = item["response"]
        if item.get("needs_rodin"):
            try:
                question = f"{title}\n{body}" if body else title
                rodin_opinion = rodin_reflect(question, response, claude_path, claude_model)
                response = f"{response}\n\n[Rodin] {rodin_opinion}"
            except Exception as e:
                log(f"Rodin error for '{title}': {e}")
        write_response_to_note(note_id, response)
        send_pushover(f"\U0001f4a1 {title}", item["pushover_summary"], config)
        tag_note(note_id, done_tag)
        log(f"Reflection answered: '{title}'")

    elif item["type"] == "task":
        tag_note(note_id, done_tag)
        task_prompt = build_task_prompt(item)
        project_path = config["frontend_path"] if item["target"] == "frontend" else config["backend_path"]
        launch_claude_code(project_path, task_prompt, note_id, item, config, title)
        log(f"Task launched: '{title}' -> {item['target']} / {item['branch_name']}")

    elif item["type"] == "clarification":
        write_response_to_note(note_id, item["questions"])
        tag_note(note_id, PENDING_TAG)
        new_title, new_body = get_note_content(note_id)
        state = load_state()
        state[note_id] = content_hash(new_title or "", new_body or "")
        save_state(state)
        send_pushover(f"\u2753 {title}", item["pushover_summary"], config)
        log(f"Clarification asked: '{title}'")


def is_pending(body):
    return f"#{PENDING_TAG}" in body


def has_user_responded(note_id, title, body):
    state = load_state()
    stored = state.get(note_id)
    if not stored:
        return True
    current = content_hash(title, body)
    if current == stored:
        return False
    del state[note_id]
    save_state(state)
    return True


def is_stable(note_id, title, body):
    time.sleep(DEBOUNCE_SECONDS)
    title2, body2 = get_note_content(note_id)
    return title == title2 and body == body2


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
    claude_model = config.get("claude_model", "")

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

        if is_pending(body):
            if not has_user_responded(note_id, title, body):
                continue
            log(f"User responded to clarification: '{title}'")
        else:
            if not is_stable(note_id, title, body):
                log(f"Note still being edited: '{title}'")
                continue

        try:
            analysis = analyze_with_claude(title, body, claude_path, claude_model)
        except Exception as e:
            log(f"Claude analysis error for '{title}': {e}")
            continue

        items = analysis.get("items", [])
        if not items:
            log(f"No items in analysis for '{title}'")
            continue

        for item in items:
            process_item(item, note_id, title, body, config)


main()
