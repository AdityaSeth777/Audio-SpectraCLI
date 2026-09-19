#!/usr/bin/env python3
"""Interactive, cross-platform launcher for the native Audio-SpectraCLI GUI.

Run directly (`python3 launch.py` / `python launch.py`), or via the
double-clickable `run.command` (macOS/Linux) or `run.bat` (Windows) wrappers
next to this file. This is an ADDITIONAL way to run the tool, alongside pip
install, Docker, and the VS Code extension — it doesn't replace any of them.

What it does:
  1. Detects the OS (macOS/Windows/Linux) and Python version.
  2. Checks the required packages are importable; if any are missing, sets
     up a local .venv next to this script and installs them there, then
     re-launches itself under that venv's Python. This sidesteps
     "externally-managed-environment" pip errors that modern
     Homebrew/python.org Python (PEP 668) and recent Linux distros raise
     when you try to pip install into the system Python directly — a very
     common first-run failure this avoids automatically instead of crashing.
  3. Lists real audio input devices (via sounddevice) and lets you pick one
     — this is hardware-specific and the GUI has no way to know it itself.
  4. Opens the GUI and starts visualizing immediately (no extra click, and
     no other prompts) — duration, sampling rate, and block size are
     already adjustable via sliders inside the GUI itself once it's open,
     so the launcher doesn't ask about them separately.
"""

import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "sounddevice": "sounddevice",
    "matplotlib": "matplotlib",
    "PyQt5": "PyQt5",
}

REPO_ROOT = Path(__file__).resolve().parent
VENV_DIR = REPO_ROOT / ".venv"


def detect_os_label():
    system = platform.system()  # 'Darwin', 'Windows', 'Linux'
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(system, system)


def _importable(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _venv_python_path(venv_dir):
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python3"


def ensure_dependencies_or_relaunch_in_venv():
    """Ensures required packages are importable in the running interpreter.

    If any are missing, offers to set up (or reuse) a local .venv and
    installs them there — never attempts to pip install into the system
    Python, since that's exactly what modern "externally-managed-
    environment" Pythons refuse to do. After installing, re-execs this
    script under the venv's Python so the rest of the run continues there.
    """
    missing = [pip_name for module_name, pip_name in REQUIRED_PACKAGES.items() if not _importable(module_name)]
    if not missing:
        return

    print(f"Missing packages: {', '.join(missing)}")
    answer = input("Set them up now in a local .venv (won't touch your system Python)? [Y/n] ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("Cannot continue without these packages. Exiting.")
        sys.exit(1)

    if not VENV_DIR.exists():
        print(f"Creating a virtual environment at {VENV_DIR} ...")
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))

    venv_python = _venv_python_path(VENV_DIR)
    print("Installing missing packages into the virtual environment (this may take a minute)...")
    subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(venv_python), "-m", "pip", "install", *missing])

    print("\nRestarting under the virtual environment...\n")
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def choose_audio_device():
    import sounddevice as sd

    devices = sd.query_devices()
    input_devices = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]

    if not input_devices:
        print("No audio input devices found on this machine. Exiting.")
        sys.exit(1)

    default_index = sd.default.device[0]
    if default_index is None or default_index < 0:
        default_index = input_devices[0][0]

    print("\nAvailable audio input devices:")
    for i, d in input_devices:
        marker = " (default)" if i == default_index else ""
        print(f"  [{i}] {d['name']}{marker}")

    choice = input(f"\nChoose a device index [Enter for default {default_index}]: ").strip()
    if not choice:
        return None  # None lets sounddevice pick its own default at stream-open time

    try:
        chosen = int(choice)
    except ValueError:
        print(f"Not a number — using default device {default_index}.")
        return None

    if chosen not in [i for i, _ in input_devices]:
        print(f"No input device with index {chosen} — using default device {default_index}.")
        return None

    return chosen


def main():
    print(f"Audio-SpectraCLI launcher — detected {detect_os_label()}, Python {platform.python_version()}\n")

    ensure_dependencies_or_relaunch_in_venv()
    device = choose_audio_device()

    from PyQt5.QtWidgets import QApplication

    from Audio_SpectraCLI import AudioSpectrumVisualizer

    # Duration/sampling rate/block size are intentionally NOT asked here —
    # the GUI already has sliders for all three once it's open, so asking
    # again in the terminal first would just be a second, redundant prompt
    # for the same settings.
    app = QApplication(sys.argv)
    window = AudioSpectrumVisualizer(device=device)
    window.show()
    window.toggle_visualization()  # start immediately — no extra click needed
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
