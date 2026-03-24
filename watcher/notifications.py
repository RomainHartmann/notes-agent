import urllib.request
import urllib.parse

from watcher.config import log


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
