#!/usr/bin/env bash
# Usage: wait-for-rebuild.sh <dev-server-log> <file-to-touch> [attempts=4] [seconds-per-attempt=120]
# After a git checkout the watcher usually compiles once mid-checkout (missing modules) and once clean.
# This waits for a NEW "compiled" line that has no "errors" in it, re-touching a file to force another
# compile when the last one was dirty. Exit 0 on a clean compile, 1 on timeout.
# Only the last few MB of the log are scanned, so a day-old multi-GB log does not slow each poll.
set -u
LOG="$1"; TOUCH="$2"; ATTEMPTS="${3:-4}"; SECS="${4:-120}"
for attempt in $(seq 1 "$ATTEMPTS"); do
  before=$(tail -c 5000000 "$LOG" | grep -c "compiled")
  touch "$TOUCH"
  for _ in $(seq 1 $((SECS / 5))); do
    sleep 5
    now=$(tail -c 5000000 "$LOG" | grep -c "compiled")
    if [ "$now" -gt "$before" ]; then
      last=$(tail -c 5000000 "$LOG" | grep "compiled" | tail -1)
      case "$last" in
        *error*) echo "attempt $attempt: dirty compile, retrying (${last:0:80})"; sleep 10; continue 2;;
        *) echo "clean compile: ${last:0:90}"; sleep 5; exit 0;;
      esac
    fi
  done
done
echo "no clean compile after $ATTEMPTS attempts"; exit 1
