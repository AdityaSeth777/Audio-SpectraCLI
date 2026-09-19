#!/usr/bin/env bash
# Canonical entry point for running the interactive launcher (launch.py)
# from a terminal on macOS/Linux: `./run.sh`.
#
# On macOS, double-clicking a plain .sh file in Finder usually opens it in
# a text editor rather than running it (Finder's default association),
# so run.command exists purely as a thin wrapper around this script for
# that double-click case — this file is the one with the actual logic.
set -e
cd "$(dirname "$0")"

if [ -x ".venv/bin/python3" ]; then
    # A previous run already set up a local venv with everything installed —
    # use it directly and skip the system-Python dependency check entirely.
    PYTHON=".venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python was not found on PATH. Install Python 3 from https://python.org and try again."
    exit 1
fi

exec "$PYTHON" launch.py
