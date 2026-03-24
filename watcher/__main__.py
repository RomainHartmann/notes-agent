from watcher.config import log, load_config
from watcher.notes import get_unprocessed_note_ids, get_note_content, write_response_to_note, tag_note
from watcher.analysis import analyze_with_claude
from watcher.tasks import build_task_prompt, launch_claude_code
from watcher.notifications import send_pushover


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


main()
