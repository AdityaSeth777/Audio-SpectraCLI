#!/usr/bin/env python3
"""Interactive, cross-platform launcher for the native Audio-SpectraCLI GUI.

Run directly (`python3 launch.py` / `python launch.py`), or via the
double-clickable `run.command` (macOS/Linux) or `run.bat` (Windows) wrappers
next to this file. This is an ADDITIONAL way to run the tool, alongside pip
install, Docker, and the VS Code extension — it doesn't replace any of them.

What it does:
  1. Detects the OS (macOS/Windows/Linux) and Python version.
  2. Checks the required packages are importable; offers to `pip install`
     any that are missing.
  3. Lists real audio input devices (via sounddevice) and lets you pick one.
  4. Prompts for duration/sampling rate/block size/color — press Enter on
     any prompt to keep the default, so hitting Enter through all of them
     launches immediately with sane defaults.
  5. Opens the GUI and starts visualizing immediately (no extra click).
"""

import platform
import subprocess
import sys

REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "sounddevice": "sounddevice",
    "matplotlib": "matplotlib",
    "PyQt5": "PyQt5",
}


def detect_os_label():
    system = platform.system()  # 'Darwin', 'Windows', 'Linux'
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(system, system)


def check_and_install_dependencies():
    missing = [pip_name for module_name, pip_name in REQUIRED_PACKAGES.items() if not _importable(module_name)]
    if not missing:
        return

    print(f"Missing packages: {', '.join(missing)}")
    answer = input("Install them now with pip? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    else:
        print("Cannot continue without these packages. Exiting.")
        sys.exit(1)


def _importable(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


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


def prompt_int(label, default):
    raw = input(f"{label} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"Not a number — using default {default}.")
        return default


def prompt_str(label, default):
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def main():
    print(f"Audio-SpectraCLI launcher — detected {detect_os_label()}, Python {platform.python_version()}\n")

    check_and_install_dependencies()
    device = choose_audio_device()

    print()
    duration = prompt_int("Duration (seconds)", 10)
    fs = prompt_int("Sampling rate (Hz)", 44100)
    block_size = prompt_int("Block size", 4096)
    color = prompt_str("Color", "blue")

    from PyQt5.QtWidgets import QApplication

    from Audio_SpectraCLI import AudioSpectrumVisualizer

    app = QApplication(sys.argv)
    window = AudioSpectrumVisualizer(duration=duration, fs=fs, block_size=block_size, color=color, device=device)
    window.show()
    window.toggle_visualization()  # start immediately — no extra click needed
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
