#!/usr/bin/env bash
# Double-click launcher for macOS/Linux — opens Terminal and runs launch.py.
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python was not found on PATH. Install Python 3 from https://python.org and try again."
    read -p "Press Enter to close..."
    exit 1
fi

"$PYTHON" launch.py
read -p "Press Enter to close..."
