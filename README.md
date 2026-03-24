# notes-watcher

I write a note on my iPhone, and the AI codes the feature and merges it automatically.

## Philosophy

The idea here is that the quality of what you build is no longer limited by the time spent coding, but by the quality of the ideas you have. A thought on the subway, an idea in the shower, a question at 11pm: instead of vanishing, they become commits. You no longer need to have your head in the code for every impulse. The idea becomes the project.

It's not always perfect. Claude Code makes a first pass, sometimes you need to iterate. But the threshold has been crossed: intent is enough to trigger the work.

## How it works

```
iPhone (Apple Notes)
    |
    v
iCloud sync
    |
    v
Mac mini (python -m watcher, every 60s)
    |
    |-- task       -> Claude Code opens a Terminal, codes and merges
    |
    +-- reflection -> response written directly in the note
```

The watcher queries Apple Notes via AppleScript, sends each unprocessed note to Claude Code for analysis (`claude -p`), then acts on the result. A note can contain multiple independent items, each processed separately.

## Features

- Automatic monitoring of an Apple Notes folder via launchd
- Intelligent analysis via Claude Code CLI (task or reflection)
- Multi-item support per note
- Claude Code launched in a dedicated Terminal per task
- Git operations hardcoded in the shell script (checkout, branch, commit, merge)
- Structured response written directly in the note for reflections
- Existing code detection (`#claude-exists`)
- Push notifications via Pushover

## Prerequisites

- macOS (Mac mini recommended, always on)
- Python 3
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- [Pushover](https://pushover.net) account

## Installation

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd notes-watcher
   ```

2. Copy and fill in the configuration:
   ```bash
   cp config.example.json config.json
   ```

3. Install the launchd agent:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

The watcher runs in the background, every 60 seconds.

## Configuration

| Field | Description |
|---|---|
| `notes_folder` | Name of the folder to watch in Apple Notes |
| `processed_tag` | Tag added to processed notes |
| `exists_tag` | Tag set when the feature already exists in the code |
| `frontend_path` | Absolute path to the frontend repo (Flutter) |
| `backend_path` | Absolute path to the backend repo |
| `dev_branch` | Target development branch |
| `claude_path` | Path to the Claude Code binary (default: `claude`) |
| `pushover_app_token` | Pushover application token |
| `pushover_user_key` | Pushover user key |

## Stack

Python · AppleScript · launchd · Claude Code CLI · Pushover · Git
