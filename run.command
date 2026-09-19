#!/usr/bin/env bash
# Double-click wrapper for macOS/Linux Finder: just runs run.sh, which has
# the actual logic (see run.sh's header comment for why this file exists
# separately). Keeping this thin means there's exactly one place — run.sh —
# that needs to change if the launch steps ever do.
cd "$(dirname "$0")"
./run.sh
read -p "Press Enter to close..."
