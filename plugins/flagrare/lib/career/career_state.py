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
MOVED_NOTE = (
    "# Moved\n\n"
    "`~/.claude/skills/flagrare/career/` now holds these files for the career skills; impact-scan (formerly senior-scan) writes there.\n"
    "This folder is kept as a backup and nothing here is deleted.\n"
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
            career_lines = {line.rstrip() for line in career_log.splitlines()}
            missing = [line for line in legacy_entries if line not in career_lines]
            if missing:
                content = career_log.rstrip('\n') + '\n' + '\n'.join(missing) + '\n'
                actions.append({"action": "write", "path": p["log"], "content": content, "reason": "append missing legacy entries to career log"})

    actions += _plan_scan_state(legacy / "state.json", Path(p["scan_state"]))
    actions += _plan_voice(legacy / "voice.md", Path(p["voice"]))

    if legacy.is_dir() and not (legacy / "MOVED.md").is_file():
        actions.append({"action": "write", "path": str(legacy / "MOVED.md"), "content": MOVED_NOTE, "reason": "pointer to the new career folder"})
    return actions


def _merge_seen(legacy: list, career: list) -> list:
    """Union of seen items by id. A contributed item wins; otherwise the later surfaced_at wins. Keeps id-less items."""
    merged: dict[str, dict] = {}
    order: list[str] = []
    legacy_id_less: list[dict] = []
    career_id_less: list[dict] = []
    seen_id_less: list[dict] = []
    for item in (legacy or []) + (career or []):
        key = item.get("id")
        if key is None:
            if not any(i == item for i in seen_id_less):
                if item in (legacy or []):
                    legacy_id_less.append(item)
                else:
                    career_id_less.append(item)
                seen_id_less.append(item)
            continue
        if key not in merged:
            merged[key] = item
            order.append(key)
            continue
        current = merged[key]
        if current.get("status") == "contributed" and item.get("status") != "contributed":
            continue
        if item.get("status") == "contributed" and current.get("status") != "contributed":
            merged[key] = item
            continue
        if str(item.get("surfaced_at", "")) >= str(current.get("surfaced_at", "")):
            merged[key] = item
    return [merged[k] for k in order] + legacy_id_less + career_id_less


def _plan_scan_state(legacy_path: Path, career_path: Path) -> list[dict]:
    """Copy or merge senior-scan's state.json into career/scan-state.json, never losing a seen item."""
    legacy_text = _read(legacy_path)
    if legacy_text is None:
        return []
    career_text = _read(career_path)
    if career_text is None:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "copy state.json from senior-scan"}]
    try:
        legacy_state = json.loads(legacy_text)
        career_state = json.loads(career_text)
    except json.JSONDecodeError:
        return []
    if not isinstance(legacy_state, dict) or not isinstance(career_state, dict):
        return []
    legacy_seen = legacy_state.get("seen")
    career_seen = career_state.get("seen")
    if legacy_seen is not None and not isinstance(legacy_seen, list):
        return []
    if career_seen is not None and not isinstance(career_seen, list):
        return []
    if legacy_seen is not None:
        for item in legacy_seen:
            if not isinstance(item, dict):
                return []
    if career_seen is not None:
        for item in career_seen:
            if not isinstance(item, dict):
                return []
    merged = {**legacy_state, **career_state}
    if "last_run" in legacy_state or "last_run" in career_state:
        merged["last_run"] = max(str(legacy_state.get("last_run") or ""), str(career_state.get("last_run") or ""))
    if "seen" in legacy_state or "seen" in career_state:
        merged["seen"] = _merge_seen(legacy_state.get("seen", []), career_state.get("seen", []))
    if merged == career_state:
        return []
    content = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    return [{"action": "write", "path": str(career_path), "content": content, "reason": "merge newer senior-scan state into career scan-state"}]


def _plan_voice(legacy_path: Path, career_path: Path) -> list[dict]:
    """Copy voice.md when missing, or when the legacy copy is newer and different."""
    legacy_text = _read(legacy_path)
    if legacy_text is None:
        return []
    career_text = _read(career_path)
    if career_text is None:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "copy voice.md from senior-scan"}]
    if legacy_text != career_text and legacy_path.stat().st_mtime > career_path.stat().st_mtime:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "legacy voice.md is newer"}]
    return []


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
