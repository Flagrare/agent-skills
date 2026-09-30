"""Shared state for the flagrare career skills.

Pure functions: this module never writes files. Skills apply the actions it
plans with the Write tool, because a sandboxed shell cannot write under
~/.claude/skills.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CAREER_REL = Path(".claude/skills/flagrare/career")
LEGACY_REL = Path(".claude/skills/flagrare/senior-scan")
CONFIG_REL = Path(".claude/skills/flagrare/config.json")
LOG_HEADER = "# Career contributions"
MOVED_NOTE = (
    "# Mirrored\n\n"
    "`~/.claude/skills/flagrare/career/` mirrors these files for the career skills.\n"
    "Senior-scan still writes here until impact-scan replaces it; nothing here is deleted.\n"
)


def paths(home: str) -> dict[str, str]:
    root = Path(home)
    career = root / CAREER_REL
    return {
        "career_dir": str(career),
        "legacy_dir": str(root / LEGACY_REL),
        "config": str(root / CONFIG_REL),
        "map_md": str(career / "promotion-map.md"),
        "map_json": str(career / "promotion-map.json"),
        "initiatives": str(career / "initiatives.json"),
        "log": str(career / "contributions.log.md"),
        "scan_state": str(career / "scan-state.json"),
        "flags": str(career / "flags.json"),
        "voice": str(career / "voice.md"),
    }


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _entries(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.rstrip() for line in text.splitlines() if line.startswith("- ")]


def _header(text: str | None) -> str | None:
    if not text:
        return None
    for line in text.splitlines():
        if line.startswith("# "):
            return line
    return None


def read_contributions(home: str) -> list[str]:
    p = paths(home)
    legacy = _entries(_read(Path(p["legacy_dir"]) / "contributions.log.md"))
    career = _entries(_read(Path(p["log"])))
    merged: list[str] = []
    seen: set[str] = set()
    for line in legacy + career:
        if line not in seen:
            seen.add(line)
            merged.append(line)
    return merged


def plan_migration(home: str) -> list[dict]:
    p = paths(home)
    career = Path(p["career_dir"])
    legacy = Path(p["legacy_dir"])
    actions: list[dict] = []
    if not career.is_dir():
        actions.append({"action": "mkdir", "path": str(career), "content": None, "reason": "create shared career state folder"})

    legacy_log = _read(legacy / "contributions.log.md")
    career_log = _read(Path(p["log"]))
    if legacy_log is not None:
        if career_log is None:
            actions.append({"action": "write", "path": p["log"], "content": legacy_log, "reason": "copy legacy contributions log to career folder"})
        else:
            legacy_entries = _entries(legacy_log)
            career_lines = set(career_log.splitlines())
            missing = [line for line in legacy_entries if line not in career_lines]
            if missing:
                content = career_log.rstrip('\n') + '\n' + '\n'.join(missing) + '\n'
                actions.append({"action": "write", "path": p["log"], "content": content, "reason": "append missing legacy entries to career log"})

    for legacy_name, target_key in (("state.json", "scan_state"), ("voice.md", "voice")):
        source = _read(legacy / legacy_name)
        if source is not None and not Path(p[target_key]).is_file():
            actions.append({"action": "write", "path": p[target_key], "content": source, "reason": f"copy {legacy_name} from senior-scan"})

    if legacy.is_dir() and not (legacy / "MOVED.md").is_file():
        actions.append({"action": "write", "path": str(legacy / "MOVED.md"), "content": MOVED_NOTE, "reason": "pointer to the new career folder"})
    return actions


def skill_config(config: dict, name: str) -> dict:
    skills = (config or {}).get("skills", {})
    if name in skills:
        return skills[name]
    if name == "impact-scan":
        return skills.get("senior-scan", {})
    return {}


def board_dir(config: dict) -> str | None:
    skills = (config or {}).get("skills", {})
    for key in ("career", "senior-scan"):
        board = skills.get(key, {}).get("board", {})
        if board.get("dir"):
            return board["dir"]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only state helper for the flagrare career skills.")
    parser.add_argument("command", choices=["paths", "contributions", "plan"])
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    if args.command == "paths":
        result: object = paths(args.home)
    elif args.command == "contributions":
        result = read_contributions(args.home)
    else:
        result = plan_migration(args.home)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
