"""What /flagrare:career should run, and the numbers its digest and the board show. Read-only.

The skill decides how to run each step (asking the user, or listing it as
pending when nobody is there to answer); this module only reads timestamps,
flags and the log, so the decision is the same every time.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path

import career_state
import initiatives
from map_schema import missing_sections, stale_sections
from scoring import open_rows, unseen_people

BALANCE_WINDOW_DAYS = 30
BALANCE_MIN_CONTRIBUTIONS = 3
NEEDS_USER = {"target", "people", "manager_questions"}
LOG_ENTRY = re.compile(r"- (\d{4}-\d{2}-\d{2}) \|.*?(?:\| row: (\S+))?$")


def _load(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _map(home: str) -> dict | None:
    m = _load(career_state.paths(home)["map_json"])
    return m if isinstance(m, dict) else None


def _log(home: str) -> list[tuple[str, str | None]]:
    """(date, row id or None) for every log entry, old and new locations together."""
    out = []
    for line in career_state.read_contributions(home):
        m = LOG_ENTRY.match(line.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def due(home: str, today: str) -> list[dict]:
    """The steps a career run takes, in order. `needs_user` steps become pending in a scheduled run."""
    steps: list[dict] = []
    m = _map(home)
    if m is None:
        steps.append({"skill": "promotion", "mode": "first_run", "sections": [], "needs_user": True,
                      "why": "no promotion map yet"})
    else:
        flags = career_state._load_list(Path(career_state.paths(home)["flags"]))
        flagged = {f.get("section") for f in flags if isinstance(f, dict)}
        missing = missing_sections(m)
        stale = stale_sections(m, date.fromisoformat(today))
        sections = [s for s in dict.fromkeys(missing + stale + sorted(s for s in flagged if s))]
        if sections:
            why = []
            if missing:
                why.append("not researched yet: " + ", ".join(missing))
            if stale:
                why.append("older than 90 days: " + ", ".join(stale))
            if flagged - set(missing) - set(stale) - {None}:
                why.append("flagged by a scan: " + ", ".join(sorted(flagged - set(missing) - set(stale) - {None})))
            steps.append({"skill": "promotion", "mode": "resume" if missing else "refresh", "sections": sections,
                          "needs_user": bool(set(sections) & NEEDS_USER) or bool(missing), "why": "; ".join(why)})
    cadence = initiatives.context(home, today)["cadence"]
    if cadence["due"]:
        since = "never run" if cadence["days_since"] is None else f"last run {cadence['days_since']} days ago"
        steps.append({"skill": "opportunity-scan", "mode": "scan", "sections": [], "needs_user": False, "why": since})
    steps.append({"skill": "impact-scan", "mode": "scan", "sections": [], "needs_user": False, "why": "every run"})
    return steps


def balance(home: str, today: str) -> dict:
    """The "all answering, nothing owned" check: recent contributions against an initiative the user owns."""
    start = (date.fromisoformat(today) - timedelta(days=BALANCE_WINDOW_DAYS - 1)).isoformat()
    recent = sum(1 for d, _ in _log(home) if start <= d <= today)
    items = [i for i in career_state._load_list(Path(career_state.paths(home)["initiatives"])) if isinstance(i, dict)]
    active = next((i for i in items if i.get("status") == "active"), None)
    warn = active is None and recent >= BALANCE_MIN_CONTRIBUTIONS
    message = (f"All answering, nothing owned: {recent} contributions in the last {BALANCE_WINDOW_DAYS} days and no initiative you own."
               if warn else "")
    return {"window_start": start, "contributions": recent, "active": active.get("id") if active else None,
            "warn": warn, "message": message}


def readiness(home: str) -> list[dict]:
    """Evidence per rubric row: log entries tagged with the row plus the row's own evidence. strong 3+, thin 1-2, empty 0."""
    m = _map(home)
    if m is None:
        return []
    tagged: dict[str, int] = {}
    for _, row in _log(home):
        if row:
            tagged[row] = tagged.get(row, 0) + 1
    out = []
    for row in ((m.get("rubric") or {}).get("rows") or []):
        if not isinstance(row, dict) or not row.get("id"):
            continue
        count = tagged.get(row["id"], 0) + len(row.get("evidence") or [])
        state = "strong" if count >= 3 else "thin" if count else "empty"
        out.append({"id": row["id"], "area": row.get("area", ""), "status": row.get("status", ""),
                    "evidence": count, "state": state})
    return out


def map_line(home: str) -> dict:
    """The one map line of the digest, and the board's promotion panel."""
    m = _map(home)
    if m is None:
        return {"has_map": False}
    cal = m.get("calendar") or {}
    talk = cal.get("manager_conversation") if isinstance(cal.get("manager_conversation"), dict) else {}
    deadline = cal.get("packet_deadline")
    return {
        "has_map": True,
        "target_level": initiatives._value((m.get("target") or {}).get("target_level")),
        "open_rows": len(open_rows(m)),
        "unseen_people": unseen_people(m),
        "talk_to_manager": {k: talk.get(k) for k in ("comfortable_by", "absolute_by", "state", "status") if talk.get(k)},
        "packet_deadline": {"value": initiatives._value(deadline), "status": deadline.get("status")} if isinstance(deadline, dict) else None,
    }


def board(home: str, today: str) -> dict:
    """What the board adds to data.json: the initiative card, the promotion panel and row coverage."""
    ctx = initiatives.context(home, today)["initiatives"]
    return {"initiatives": {"active": ctx["active"], "proposed": ctx["proposed"]},
            "promotion": map_line(home), "readiness": readiness(home), "balance": balance(home, today)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only inputs for /flagrare:career.")
    parser.add_argument("command", choices=["due", "balance", "readiness", "map", "board"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", required=True)
    args = parser.parse_args()
    try:
        date.fromisoformat(args.today)
    except ValueError:
        parser.error("--today must be YYYY-MM-DD")
    result = {
        "due": lambda: due(args.home, args.today),
        "balance": lambda: balance(args.home, args.today),
        "readiness": lambda: readiness(args.home),
        "map": lambda: map_line(args.home),
        "board": lambda: board(args.home, args.today),
    }[args.command]()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
