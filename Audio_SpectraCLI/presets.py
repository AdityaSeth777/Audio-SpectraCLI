# Aditya Seth
# Description: Named-preset CRUD for the GUI's "current settings" dict
# (the same shape main.py's save_preset/load_preset file picker already
# reads and writes). This module gives that dict a fixed on-disk home so
# presets can be listed, saved under a name, renamed and deleted, instead
# of always round-tripping through an arbitrary file-picker path.
#
# Also doubles as the hardware-tuning knob: BUILTIN_PRESETS ships a
# "Low Power" preset (small block_size, no smoothing) for lower-RAM
# machines, alongside the existing default and a "High Detail" one for
# machines with more headroom.

import json
import os
import re

PRESETS_DIRNAME = ".audiospectra_cli"
PRESETS_SUBDIR = "presets"
_NAME_SANITIZE_RE = re.compile(r'[/\\:*?"<>|\x00-\x1f]+')

# Seeded into the presets directory the first time it's created. After
# that, these are just regular presets - editable, renameable, deletable
# like any other. There's nothing special about them at runtime.
BUILTIN_PRESETS = {
    "Balanced (default)": {
        "block_size": 4096,
        "window_type": "hann",
        "smoothing_enabled": True,
        "smoothing_sigma": 2,
    },
    "Low Power (8GB Macs, older hardware)": {
        "block_size": 2048,
        "window_type": "hann",
        "smoothing_enabled": False,
        "smoothing_sigma": 0,
    },
    "High Detail (16GB+ Macs, dedicated hardware)": {
        "block_size": 8192,
        "window_type": "blackman",
        "smoothing_enabled": True,
        "smoothing_sigma": 3,
    },
}


def get_presets_dir():
    """Returns the on-disk presets directory, creating (and seeding) it
    on first use. Honors AUDIOSPECTRA_CLI_HOME for tests/CI so this never
    touches a real home directory unless that's actually intended.
    """
    home = os.environ.get("AUDIOSPECTRA_CLI_HOME") or os.path.expanduser("~")
    directory = os.path.join(home, PRESETS_DIRNAME, PRESETS_SUBDIR)
    is_new = not os.path.isdir(directory)
    os.makedirs(directory, exist_ok=True)
    if is_new:
        for name, settings in BUILTIN_PRESETS.items():
            try:
                save_preset(directory, name, settings)
            except OSError:
                pass  # best-effort seeding; an empty list is still usable
    return directory


def _preset_path(directory, name):
    safe = _NAME_SANITIZE_RE.sub("", name).strip()
    if not safe:
        raise ValueError("Preset name must contain at least one letter, number, space, '.', '_' or '-'.")
    return os.path.join(directory, safe + ".json")


def list_presets(directory=None):
    """Returns preset names present on disk, sorted case-insensitively."""
    directory = directory or get_presets_dir()
    names = [
        os.path.splitext(fname)[0]
        for fname in os.listdir(directory)
        if fname.endswith(".json")
    ]
    return sorted(names, key=str.casefold)


def save_preset(directory, name, settings):
    """Writes (or overwrites) a named preset. `directory` may be None to
    use the default presets directory.
    """
    directory = directory or get_presets_dir()
    path = _preset_path(directory, name)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)
    return path


def load_preset(directory, name):
    directory = directory or get_presets_dir()
    path = _preset_path(directory, name)
    with open(path) as f:
        return json.load(f)


def delete_preset(directory, name):
    directory = directory or get_presets_dir()
    path = _preset_path(directory, name)
    os.remove(path)


def rename_preset(directory, old_name, new_name):
    directory = directory or get_presets_dir()
    old_path = _preset_path(directory, old_name)
    new_path = _preset_path(directory, new_name)
    if os.path.exists(new_path):
        raise FileExistsError(f"A preset named '{new_name}' already exists.")
    os.rename(old_path, new_path)
