import os
import subprocess
import tempfile


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
    with open(tmp_path, encoding="mac_roman") as f:
        content = f.read()
    os.remove(tmp_path)
    parts = content.split("\n---SEP---\n", 1)
    title = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    return title, body


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


def tag_note(note_id, tag):
    script = f'''tell application "Notes"
    set aNote to note id "{note_id}"
    set b to body of aNote
    set AppleScript's text item delimiters to "</div>"
    set parts to text items of b
    set firstPart to item 1 of parts
    set restText to (rest of parts) as text
    set AppleScript's text item delimiters to ""
    set body of aNote to firstPart & "</div><div>#{tag}</div>" & restText
end tell'''
    run_applescript(script)


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
