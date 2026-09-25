#!/usr/bin/env python3
"""Set the flagrare plugin version and verify the file is valid JSON.

Usage: scripts/bump-version.py 1.41.0

Releases used to edit plugin.json by hand or with shell redirects, and two of them
(v1.39.1, v1.40.1) shipped it empty. This reads the last committed file when the
working copy is empty, writes the new version to a temp file, re-reads it, and only
then replaces plugin.json.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

PATH = pathlib.Path(__file__).resolve().parent.parent / "plugins/flagrare/.claude-plugin/plugin.json"

def load():
    text = PATH.read_text() if PATH.exists() else ""
    if text.strip():
        return json.loads(text)
    # Empty file: recover from the most recent commit where it was valid JSON.
    shas = subprocess.run(["git", "log", "--format=%H", "--", str(PATH)], capture_output=True, text=True, cwd=PATH.parent, check=True).stdout.split()
    for sha in shas:
        blob = subprocess.run(["git", "show", f"{sha}:plugins/flagrare/.claude-plugin/plugin.json"], capture_output=True, text=True, cwd=PATH.parents[3])
        if blob.returncode == 0 and blob.stdout.strip():
            return json.loads(blob.stdout)
    sys.exit("plugin.json is empty and no valid version exists in git history")

def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        sys.exit("usage: bump-version.py X.Y.Z")
    data = load()
    data["version"] = sys.argv[1]
    fd, tmp = tempfile.mkstemp(dir=PATH.parent, suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    if json.loads(pathlib.Path(tmp).read_text())["version"] != sys.argv[1]:
        os.unlink(tmp)
        sys.exit("verification failed; plugin.json left unchanged")
    os.replace(tmp, PATH)
    print(f"plugin.json -> {sys.argv[1]}")

if __name__ == "__main__":
    main()
