# Aditya Seth
# Description: Named CRUD for "which input device + what settings" -
# e.g. one profile per machine/mic setup. Deliberately keyed by device
# NAME rather than sounddevice's numeric index: a profile saved on one
# machine (say, an M4 with an external interface at index 2) can't rely
# on the same index meaning the same device on a different machine (say,
# an M2 with only its built-in mic, at index 0) - device order isn't
# portable, but the name usually is close enough to match against
# whatever's actually plugged in when the profile is loaded.

import json
import os
import re

PROFILES_DIRNAME = ".audiospectra_cli"
PROFILES_SUBDIR = "device_profiles"
_NAME_SANITIZE_RE = re.compile(r'[/\\:*?"<>|\x00-\x1f]+')


def get_profiles_dir():
    home = os.environ.get("AUDIOSPECTRA_CLI_HOME") or os.path.expanduser("~")
    directory = os.path.join(home, PROFILES_DIRNAME, PROFILES_SUBDIR)
    os.makedirs(directory, exist_ok=True)
    return directory


def _profile_path(directory, name):
    safe = _NAME_SANITIZE_RE.sub("", name).strip()
    if not safe:
        raise ValueError("Device profile name must contain at least one letter, number, space, '.', '_' or '-'.")
    return os.path.join(directory, safe + ".json")


def list_profiles(directory=None):
    directory = directory or get_profiles_dir()
    names = [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith(".json")]
    return sorted(names, key=str.casefold)


def save_profile(directory, name, device_name, fs, channel_mode):
    """`device_name` is the human-readable device name (not sounddevice's
    numeric index - see module docstring)."""
    directory = directory or get_profiles_dir()
    path = _profile_path(directory, name)
    with open(path, "w") as f:
        json.dump({"device_name": device_name, "fs": fs, "channel_mode": channel_mode}, f, indent=2)
    return path


def load_profile(directory, name):
    directory = directory or get_profiles_dir()
    with open(_profile_path(directory, name)) as f:
        return json.load(f)


def delete_profile(directory, name):
    directory = directory or get_profiles_dir()
    os.remove(_profile_path(directory, name))


__all__ = ["get_profiles_dir", "list_profiles", "save_profile", "load_profile", "delete_profile"]
