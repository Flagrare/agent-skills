#!/bin/sh
# Build the demo Career Board from the fictional fixture in this folder.
# Everything in it is invented: Sam Rivera, Spokewise and every link.
# The date is fixed so the page looks the same on every build.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
python3 "$here/../build.py" "$here" --home "$here/home" --today 2026-11-12
echo "open $here/board.html"
