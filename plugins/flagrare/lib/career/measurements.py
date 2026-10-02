"""Measurements of the impact of the user's work, for /flagrare:measure-impact.

Plan-only, like career_state.py: nothing here writes a file. Commands print planned writes
of career/measurements.json as JSON, and the skill applies them with the Write tool.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path

import career_state

STAGES = ["before", "after", "past", "skipped"]
CONFIDENCE = ["direct", "supported", "inferred", "speculative", "unknown"]
OWNERSHIP = ["mine", "team", "contributed"]
KINDS = ["ticket", "tdd", "project", "log_entry"]
VERDICTS = ["worked", "didnt_work", "cant_tell"]
CHECK_DAYS = (14, 42)
BET_WAIT_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OFF_VALUES = (False, "false", "off", "no", "0", 0)


class CorruptFile(ValueError):
    """measurements.json exists but can't be read; never plan over it."""


def reminders_on(home: str) -> bool:
    """`skills["measure-impact"].reminders` in the shared config; a missing or unreadable config means on."""
    try:
        config = json.loads(Path(career_state.paths(home)["config"]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    block = ((config.get("skills") or {}).get("measure-impact") or {}) if isinstance(config, dict) else {}
    value = block.get("reminders", True) if isinstance(block, dict) else True
    return (value.strip().lower() if isinstance(value, str) else value) not in OFF_VALUES


def file_path(home: str) -> Path:
    return Path(career_state.paths(home)["measurements"])


def load(home: str) -> list[dict]:
    path = file_path(home)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorruptFile(f"{path} is not valid JSON ({exc.msg}); fix or move it before measuring again") from exc
    if not isinstance(data, list):
        raise CorruptFile(f"{path} must hold a list of measurements")
    return data


def _check_date(name: str, value: object) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValueError(f"{name} must be a date written YYYY-MM-DD")
    date.fromisoformat(value)


def _check_confidence(name: str, block: object) -> None:
    if not isinstance(block, dict) or "confidence" not in block:
        return
    if block["confidence"] not in CONFIDENCE:
        raise ValueError(f"{name} confidence must be one of {CONFIDENCE}")


def check_entry(entry: dict) -> None:
    if not isinstance(entry, dict) or not entry.get("id"):
        raise ValueError("a measurement needs an id")
    work = entry.get("work") or {}
    if not work.get("title"):
        raise ValueError("work needs a title")
    if work.get("kind") not in KINDS:
        raise ValueError(f"work kind must be one of {KINDS}")
    if entry.get("stage") not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    if "ownership" in entry and entry["ownership"] not in OWNERSHIP:
        raise ValueError(f"ownership must be one of {OWNERSHIP}")
    for name in ("baseline", "comparable", "bet", "result"):
        _check_confidence(name, entry.get(name))
    _check_date("baseline as_of", (entry.get("baseline") or {}).get("as_of"))
    _check_date("source run_at", (entry.get("source") or {}).get("run_at"))
    _check_date("launch_date", entry.get("launch_date"))


SECRET_RE = re.compile(
    r"(authorization\s*:|bearer\s+\S"
    r"|(password|passwd|pwd|api[_-]?key|secret|token)[\"']?\s*[=:]"
    r"|--password[=\s]+\S|(^|\s)-u\s+[^\s:]+:\S+"
    r"|://[^/\s:@]+:[^/\s@]+@"
    r"|\bgh[pousr]_[A-Za-z0-9]{10,}|\bAKIA[0-9A-Z]{12,}|\bxox[abpr]-[A-Za-z0-9-]{10,})",
    re.IGNORECASE,
)
SCRIPT_OWNED = ("checks", "launch_date", "created_at")


def check_query(query: str) -> None:
    if query and SECRET_RE.search(query):
        raise ValueError("the query looks like it contains a credential; save it without the secret (use an env var or a connection name)")


def _write(home: str, items: list[dict], reason: str) -> list[dict]:
    return [{"action": "write", "path": str(file_path(home)),
             "content": json.dumps(items, indent=2, ensure_ascii=False) + "\n", "reason": reason}]


def plan_upsert(home: str, entry: dict, today: str) -> list[dict]:
    _check_date("today", today)
    check_entry(entry)
    check_query((entry.get("source") or {}).get("query", ""))
    items = load(home)
    for i, current in enumerate(items):
        if isinstance(current, dict) and current.get("id") == entry["id"]:
            merged = {**current, **entry}
            for owned in SCRIPT_OWNED:
                if owned in current:
                    merged[owned] = current[owned]
                else:
                    merged.pop(owned, None)
            if current.get("stage") == "after" and entry.get("stage") == "before":
                merged["stage"] = "after"
            merged["updated_at"] = today
            items[i] = merged
            return _write(home, items, f"update measurement {entry['id']}")
    items.append({**{k: v for k, v in entry.items() if k not in SCRIPT_OWNED}, "created_at": today, "updated_at": today})
    return _write(home, items, f"save measurement {entry['id']}")


def _find(items: list[dict], item_id: str) -> dict:
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            return item
    raise ValueError(f"no measurement with id {item_id}")


def _days_after(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def plan_launch(home: str, item_id: str, launch_date: str, today: str) -> list[dict]:
    _check_date("launch_date", launch_date)
    _check_date("today", today)
    items = load(home)
    item = _find(items, item_id)
    current = [c for c in item.get("checks") or [] if isinstance(c, dict)]
    done_by_offset = {}
    for i, check in enumerate(sorted(current, key=lambda c: c.get("due") or "")):
        offset = check.get("after_days", CHECK_DAYS[i] if i < len(CHECK_DAYS) else None)
        if check.get("done_at") and offset is not None:
            done_by_offset[offset] = check
    item["launch_date"] = launch_date
    item["checks"] = [done_by_offset.get(n) or {"due": _days_after(launch_date, n), "done_at": None, "value": None,
                                                "verdict": None, "after_days": n} for n in CHECK_DAYS]
    item["updated_at"] = today
    return _write(home, items, f"set launch of {item_id} to {launch_date}")


def plan_check(home: str, item_id: str, due: str, value: str, verdict: str, today: str) -> list[dict]:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    _check_date("due", due)
    _check_date("today", today)
    items = load(home)
    item = _find(items, item_id)
    for check in item.get("checks") or []:
        if isinstance(check, dict) and check.get("due") == due:
            check.update({"done_at": today, "value": value, "verdict": verdict})
            item["stage"] = "after"
            item["updated_at"] = today
            return _write(home, items, f"record the {due} check of {item_id}: {verdict}")
    raise ValueError(f"no check due on {due} for {item_id}")


def plan_skip(home: str, item_id: str, title: str, link: str, kind: str, reason: str, today: str) -> list[dict]:
    if kind not in KINDS:
        raise ValueError(f"work kind must be one of {KINDS}")
    if not reason:
        raise ValueError("a skip needs a reason")
    _check_date("today", today)
    items = load(home)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            item.update({"stage": "skipped", "skipped_reason": reason, "updated_at": today})
            return _write(home, items, f"skip {item_id}")
    items.append({"id": item_id, "work": {"title": title, "link": link, "kind": kind}, "stage": "skipped",
                  "skipped_reason": reason, "created_at": today, "updated_at": today})
    return _write(home, items, f"skip {item_id}")


LINK_RE = re.compile(r"https?://\S+")


def _log_link(line: str) -> str:
    parts = [p.strip() for p in line[2:].split("|")] if line.startswith("- ") else []
    if len(parts) < 2:
        return ""
    found = LINK_RE.search(parts[1])
    return found.group(0).rstrip(").,;") if found else ""


WINS_WINDOW_DAYS = 30


def due(home: str, today: str, wins_since: str | None = None) -> dict:
    """What needs the user now. Log entries count as wins with no number only from `wins_since` on.
    By default that is the later of 30 days ago and the first saved measurement, and nothing before the
    user has saved one, so an old log is not reported all at once; pass "" for every entry."""
    _check_date("today", today)
    items = [i for i in load(home) if isinstance(i, dict)]
    count_wins = True
    if wins_since is None:
        window = (date.fromisoformat(today) - timedelta(days=WINS_WINDOW_DAYS)).isoformat()
        starts = sorted(str(i["created_at"]) for i in items if i.get("created_at"))
        count_wins = bool(items)
        wins_since = max(window, starts[0]) if starts else window
    known_links = {((i.get("work") or {}).get("link") or "").rstrip(").,;") for i in items}
    checks_due, waiting = [], []
    wait_cutoff = (date.fromisoformat(today) - timedelta(days=BET_WAIT_DAYS)).isoformat()
    for item in items:
        if item.get("stage") == "skipped":
            continue
        title = (item.get("work") or {}).get("title", "")
        for check in item.get("checks") or []:
            if isinstance(check, dict) and not check.get("done_at") and check.get("due") and check["due"] <= today:
                checks_due.append({"id": item.get("id"), "title": title, "due": check["due"]})
        created = item.get("created_at") or ""
        if item.get("stage") == "before" and not item.get("launch_date") and created and created <= wait_cutoff:
            waiting.append({"id": item.get("id"), "title": title, "since": created})
    wins = []
    for line in career_state.read_contributions(home) if count_wins else []:
        link = _log_link(line)
        parts = [p.strip() for p in line[2:].split("|")]
        if wins_since and (parts[0] if parts else "") < wins_since:
            continue
        if link and link not in known_links:
            wins.append({"date": parts[0], "link": link, "text": parts[2] if len(parts) > 2 else ""})
    return {"checks_due": checks_due, "bets_waiting": waiting, "unmeasured_wins": wins,
            "count": len(checks_due) + len(waiting) + len(wins)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only helper for /flagrare:measure-impact.")
    parser.add_argument("command", choices=["plan", "launch", "check", "skip", "due", "show"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today")
    parser.add_argument("--entry", help="plan: the measurement as a JSON object")
    parser.add_argument("--entry-file", help="plan: a file holding the measurement JSON (use this when the query has quotes)")
    parser.add_argument("--all-wins", action="store_true", help="due: count every log entry, not only the last 30 days")
    parser.add_argument("--id")
    parser.add_argument("--launch-date")
    parser.add_argument("--due")
    parser.add_argument("--value", default="")
    parser.add_argument("--verdict")
    parser.add_argument("--title", default="")
    parser.add_argument("--link", default="")
    parser.add_argument("--kind")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    try:
        if args.command == "show":
            result: object = load(args.home)
        elif not args.today:
            parser.error(f"{args.command} needs --today")
        elif args.command == "due":
            result = due(args.home, args.today, "" if args.all_wins else None)
        elif args.command == "plan":
            text = Path(args.entry_file).read_text(encoding="utf-8") if args.entry_file else (args.entry or "")
            try:
                entry = json.loads(text)
            except json.JSONDecodeError as exc:
                parser.error(f"--entry is not valid JSON: {exc}")
            result = plan_upsert(args.home, entry, args.today)
        elif args.command == "launch":
            result = plan_launch(args.home, args.id or "", args.launch_date or "", args.today)
        elif args.command == "check":
            result = plan_check(args.home, args.id or "", args.due or "", args.value, args.verdict or "", args.today)
        else:
            result = plan_skip(args.home, args.id or "", args.title, args.link, args.kind or "", args.reason, args.today)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
