# Aditya Seth
# Description: A local, append-only log of past visualization sessions
# (one JSON object per line), so "what was I listening to, on what
# device, for how long, last time" doesn't disappear the moment the
# window closes. Read-heavy (list/clear), the only "create" is
# append_session - there's no per-entry update, sessions are a record of
# what happened, not something to edit after the fact.

import json
import os
import time

HISTORY_DIRNAME = ".audiospectra_cli"
HISTORY_FILENAME = "session_history.jsonl"


def get_history_path():
    """Returns the session-history file path. Honors AUDIOSPECTRA_CLI_HOME
    for tests/CI, same as presets.get_presets_dir.
    """
    home = os.environ.get("AUDIOSPECTRA_CLI_HOME") or os.path.expanduser("~")
    directory = os.path.join(home, HISTORY_DIRNAME)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, HISTORY_FILENAME)


def append_session(duration_seconds, device_name=None, avg_bpm=None, path=None):
    """Appends one session record. Never raises on a write failure (a full
    disk or unwritable home directory shouldn't stop the app from working,
    it should just mean this session isn't logged).
    """
    record = {
        "ended_at": time.time(),
        "duration_seconds": round(duration_seconds, 1),
        "device_name": device_name,
        "avg_bpm": round(avg_bpm, 1) if avg_bpm else None,
    }
    try:
        with open(path or get_history_path(), "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass
    return record


def list_sessions(limit=20, path=None):
    """Returns up to `limit` most recent sessions, newest first. Skips (does
    not raise on) any malformed line, e.g. from an interrupted write.
    """
    history_path = path or get_history_path()
    if not os.path.isfile(history_path):
        return []

    records = []
    with open(history_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    records.reverse()
    return records[:limit]


def clear_history(path=None):
    history_path = path or get_history_path()
    try:
        os.remove(history_path)
    except FileNotFoundError:
        pass


__all__ = ["append_session", "list_sessions", "clear_history", "get_history_path"]
