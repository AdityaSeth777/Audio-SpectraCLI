# Aditya Seth
# Description: A local, append-only record of files this app has written
# out (PNG/CSV exports, WAV recordings), so "where did I save that" and
# "let me get rid of my old exports" don't require remembering an
# arbitrary file-picker path. Same append-only-log shape as
# session_history.py, for the same reason: these are records of what
# happened, not something to edit after the fact - only delete.

import json
import os
import time

MANIFEST_DIRNAME = ".audiospectra_cli"
MANIFEST_FILENAME = "export_manifest.jsonl"


def get_manifest_path():
    """Honors AUDIOSPECTRA_CLI_HOME for tests/CI, same as presets/session_history."""
    home = os.environ.get("AUDIOSPECTRA_CLI_HOME") or os.path.expanduser("~")
    directory = os.path.join(home, MANIFEST_DIRNAME)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, MANIFEST_FILENAME)


def record_export(export_type, file_path, path=None):
    """Appends a record for a successfully-written file. `export_type` is
    one of "png", "csv", "wav" (not enforced - just what main.py passes).
    Never raises on a write failure, same reasoning as session_history.
    """
    record = {"exported_at": time.time(), "type": export_type, "path": file_path}
    try:
        with open(path or get_manifest_path(), "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass
    return record


def list_exports(limit=50, path=None, only_existing=False):
    """Returns up to `limit` most recent export records, newest first.
    Skips malformed lines. With only_existing=True, also drops records
    whose file no longer exists on disk (e.g. since deleted or moved).
    """
    manifest_path = path or get_manifest_path()
    if not os.path.isfile(manifest_path):
        return []

    records = []
    with open(manifest_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    records.reverse()
    if only_existing:
        records = [r for r in records if os.path.isfile(r.get("path", ""))]
    return records[:limit]


def delete_export(file_path, path=None):
    """Removes the file from disk (if present) and drops every manifest
    record pointing at it. Returns True if the file itself was removed.
    """
    manifest_path = path or get_manifest_path()
    removed = False
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            removed = True
        except OSError:
            pass

    if os.path.isfile(manifest_path):
        remaining = [r for r in list_exports(limit=None or 10**9, path=manifest_path) if r.get("path") != file_path]
        remaining.reverse()  # list_exports returns newest-first; the file stores oldest-first
        with open(manifest_path, "w") as f:
            for record in remaining:
                f.write(json.dumps(record) + "\n")

    return removed


__all__ = ["record_export", "list_exports", "delete_export", "get_manifest_path"]
