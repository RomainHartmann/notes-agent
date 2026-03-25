import hashlib
import json
import os

from watcher.config import BASE_DIR

STATE_PATH = os.path.join(BASE_DIR, "state.json")


def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def content_hash(title, body):
    return hashlib.sha256(f"{title}\n{body}".encode()).hexdigest()
