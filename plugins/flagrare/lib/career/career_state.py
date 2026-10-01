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
        "opportunity_state": str(career / "opportunity-state.json"),
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

    if legacy.is_dir():
        moved = _read(legacy / "MOVED.md")
        if moved is None:
            actions.append({"action": "write", "path": str(legacy / "MOVED.md"), "content": MOVED_NOTE, "reason": "pointer to the new career folder"})
        elif moved.startswith("# Mirrored"):
            actions.append({"action": "write", "path": str(legacy / "MOVED.md"), "content": MOVED_NOTE, "reason": "refresh the pointer note"})
    return actions


class _Slot:
    def __init__(self, item: dict) -> None:
        self.item = item


def _hashable(value: object) -> bool:
    try:
        hash(value)
    except TypeError:
        return False
    return True


def _merge_seen(legacy: list, career: list) -> list:
    """Union of seen items by id. A contributed item wins; otherwise the later surfaced_at wins, and the career copy wins a tie.
    Career order is kept and new legacy items are appended. Items without a usable (present and hashable) id are kept."""
    merged: dict = {}
    result: list = []
    for item in list(career or []) + list(legacy or []):
        key = item.get("id")
        if key is None or not _hashable(key):
            if item not in [r for r in result if not isinstance(r, _Slot)]:
                result.append(item)
            continue
        if key not in merged:
            slot = _Slot(item)
            merged[key] = slot
            result.append(slot)
            continue
        slot = merged[key]
        current = slot.item
        if current.get("status") == "contributed" and item.get("status") != "contributed":
            continue
        if item.get("status") == "contributed" and current.get("status") != "contributed":
            slot.item = item
            continue
        if str(item.get("surfaced_at", "")) > str(current.get("surfaced_at", "")):
            slot.item = item
    return [r.item if isinstance(r, _Slot) else r for r in result]


def _canon(items: list) -> list[str]:
    return sorted(json.dumps(i, sort_keys=True, ensure_ascii=False) for i in items)


def _same_state(merged: dict, career: dict) -> bool:
    if merged.keys() != career.keys():
        return False
    for key, value in merged.items():
        if key == "seen":
            if _canon(value) != _canon(career["seen"]):
                return False
        elif value != career[key]:
            return False
    return True


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
    if _same_state(merged, career_state):
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


def _load_list(path: Path) -> list:
    text = _read(path)
    if text is None:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def plan_flag(home: str, section: str, reason: str, source: str, today: str) -> list[dict]:
    """Plan flags.json with one more staleness flag. A flag for the same section with the same reason or the same source is not added twice."""
    from map_schema import SECTIONS
    if section not in SECTIONS:
        raise ValueError(f"section must be one of {SECTIONS}")
    path = Path(paths(home)["flags"])
    flags = _load_list(path)
    for f in flags:
        if isinstance(f, dict) and f.get("section") == section and (f.get("reason") == reason or (source and f.get("source") == source)):
            return []
    flags.append({"section": section, "reason": reason, "source": source, "raised_at": today})
    return [{"action": "write", "path": str(path), "content": json.dumps(flags, indent=2, ensure_ascii=False) + "\n", "reason": f"flag {section} as possibly stale"}]


def plan_candidate(home: str, item_id: str, title: str, evidence: str, today: str, details: dict | None = None) -> list[dict]:
    """Plan initiatives.json with one sighting of a problem: add it, or, for a new evidence link, bump seen_count and add the link. The same link again changes nothing.

    `details` are the proposal fields an opportunity scan drafted but the user has not decided on yet. They are kept as
    `draft_proposal` on items that are still candidates, without counting as a sighting, and never replace a kept `proposal`.
    """
    if details and "score" in details:
        from initiatives import check_score
        check_score(details["score"])
    path = Path(paths(home)["initiatives"])
    items = _load_list(path)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            changed = False
            links = item.setdefault("evidence", [])
            if evidence and evidence not in links:
                links.append(evidence)
                item["seen_count"] = int(item.get("seen_count", 1)) + 1
                item["last_seen"] = today
                changed = True
            if details and item.get("status") == "candidate" and item.get("draft_proposal") != details:
                item["draft_proposal"] = details
                changed = True
            if not changed:
                return []
            break
    else:
        item = {"id": item_id, "title": title, "evidence": [evidence] if evidence else [], "seen_count": 1,
                "first_seen": today, "last_seen": today, "status": "candidate"}
        if details:
            item["draft_proposal"] = details
        items.append(item)
    return [{"action": "write", "path": str(path), "content": json.dumps(items, indent=2, ensure_ascii=False) + "\n", "reason": f"record a sighting of {item_id}"}]

def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only state helper for the flagrare career skills.")
    parser.add_argument("command", choices=["paths", "contributions", "plan", "flag", "candidate"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--section")
    parser.add_argument("--reason")
    parser.add_argument("--source", default="")
    parser.add_argument("--id")
    parser.add_argument("--title")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--today")
    parser.add_argument("--details", help="candidate: the drafted proposal fields as a JSON object")
    args = parser.parse_args()
    if args.command == "paths":
        result: object = paths(args.home)
    elif args.command == "contributions":
        result = read_contributions(args.home)
    elif args.command == "plan":
        result = plan_migration(args.home)
    elif args.command == "flag":
        if not (args.section and args.reason and args.today):
            parser.error("flag needs --section, --reason and --today")
        try:
            result = plan_flag(args.home, args.section, args.reason, args.source, args.today)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        if not (args.id and args.title and args.today):
            parser.error("candidate needs --id, --title and --today")
        details = None
        if args.details:
            try:
                details = json.loads(args.details)
            except json.JSONDecodeError as exc:
                parser.error(f"--details is not valid JSON: {exc}")
            if not isinstance(details, dict):
                parser.error("--details must be a JSON object")
        result = plan_candidate(args.home, args.id, args.title, args.evidence, args.today, details)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
