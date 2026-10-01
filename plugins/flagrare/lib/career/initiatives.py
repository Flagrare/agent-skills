"""Inputs and planned writes for opportunity-scan. Never writes files.

The model still judges which problems are worth owning and how to pitch them;
this module lists what the ranking reads (the promotion map, the initiatives
already recorded, the cadence) and plans the initiatives.json and
opportunity-state.json content the skill writes with the Write tool.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import career_state
from scoring import open_rows, unseen_people

CADENCE_DAYS = 30
WINDOW_CAP_DAYS = 90
REQUIRED = ["problem", "hypothesis", "metric", "first_step", "pitch", "owner_check"]
MOVES = {
    ("candidate", "dropped"), ("proposed", "dropped"),
    ("proposed", "active"), ("active", "done"), ("active", "dropped"),
    ("dropped", "candidate"), ("dropped", "dropped"),
}


def _value(fact: object) -> object:
    """A fact's value, every alternative's value when sources disagree, or the plain value itself."""
    if isinstance(fact, dict):
        if "value" in fact:
            return fact["value"]
        if isinstance(fact.get("alternatives"), list):
            return [a.get("value") for a in fact["alternatives"] if isinstance(a, dict)]
        return None
    return fact


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _items(home: str) -> list:
    return career_state._load_list(Path(career_state.paths(home)["initiatives"]))


def _write(path: str, data: object, reason: str) -> list[dict]:
    return [{"action": "write", "path": path, "content": json.dumps(data, indent=2, ensure_ascii=False) + "\n", "reason": reason}]


def _cadence(home: str, today: str, cadence_days: int) -> dict:
    state = _load_json(Path(career_state.paths(home)["opportunity_state"]))
    last_run = state.get("last_run") if isinstance(state, dict) else None
    now = date.fromisoformat(today)
    try:
        since = max(0, (now - date.fromisoformat(str(last_run))).days) if last_run else None
    except ValueError:
        since = None
    start = now - timedelta(days=cadence_days) if since is None else now - timedelta(days=min(since, WINDOW_CAP_DAYS))
    next_due = (now if since is None else now + timedelta(days=max(0, cadence_days - since))).isoformat()
    return {"last_run": last_run if since is not None else None, "days_since": since, "cadence_days": cadence_days,
            "due": since is None or since >= cadence_days, "next_due": next_due, "window_start": start.isoformat()}


def context(home: str, today: str) -> dict:
    """What opportunity-scan ranks against: the map (when there is one), the initiatives so far, the cadence, and the impact-scan config as fallback."""
    p = career_state.paths(home)
    config = _load_json(Path(p["config"]))
    config = config if isinstance(config, dict) else {}
    own = career_state.skill_config(config, "opportunity-scan")
    scan = career_state.skill_config(config, "impact-scan")
    try:
        cadence_days = max(1, int(own.get("cadence_days", CADENCE_DAYS))) if isinstance(own, dict) else CADENCE_DAYS
    except (TypeError, ValueError):
        cadence_days = CADENCE_DAYS
    scan = scan if isinstance(scan, dict) else {}
    items = [i for i in _items(home) if isinstance(i, dict) and i.get("id")]
    by_status = lambda s: [i for i in items if i.get("status") == s]
    dropped = [{**i, "seen_again": str(i.get("last_seen", "")) > str(i.get("dropped_at", ""))} for i in by_status("dropped")]
    result = {
        "has_map": False,
        "target": {}, "open_rows": [], "unseen_people": [],
        "decision_process": None, "packet_deadline": None,
        "initiatives": {
            "active": (by_status("active") or [None])[0],
            "proposed": by_status("proposed"),
            "candidates": sorted(by_status("candidate"), key=lambda i: -int(i.get("seen_count") or 0)),
            "dropped": dropped,
        },
        "cadence": _cadence(home, today, cadence_days),
        "fallback": {"target_behaviors": scan.get("target_behaviors", []), "domains": scan.get("domains", []),
                     "audience": scan.get("audience", [])},
    }
    m = _load_json(Path(p["map_json"]))
    if not isinstance(m, dict):
        return result
    target = m.get("target") or {}
    process = m.get("process") or {}
    calendar = m.get("calendar") or {}
    decision = process.get("decision_process") if isinstance(process, dict) else None
    deadline = calendar.get("packet_deadline") if isinstance(calendar, dict) else None
    result.update({
        "has_map": True,
        "target": {k: _value(target.get(k)) for k in ("target_level", "cycle", "why", "more_of", "less_of") if target.get(k) is not None},
        "open_rows": open_rows(m),
        "unseen_people": unseen_people(m),
        "decision_process": {k: _value(v) for k, v in decision.items()} if isinstance(decision, dict) else None,
        "packet_deadline": {"value": _value(deadline), "status": deadline.get("status")} if isinstance(deadline, dict) else None,
    })
    return result


def plan_propose(home: str, item_id: str, title: str, evidence: list[str], proposal: dict, today: str) -> list[dict]:
    """Plan initiatives.json with a proposal: a new item, or a candidate (or one dropped and seen again) moved to proposed, keeping its sightings."""
    missing = [k for k in REQUIRED if not proposal.get(k)]
    if missing:
        raise ValueError(f"proposal is missing {', '.join(missing)}")
    path = career_state.paths(home)["initiatives"]
    items = _items(home)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            status = item.get("status")
            if status == "dropped" and not str(item.get("last_seen", "")) > str(item.get("dropped_at", "")):
                raise ValueError(f"{item_id} was dropped on {item.get('dropped_at')} and not seen since; reopen it first")
            if status in ("active", "done"):
                raise ValueError(f"{item_id} is already {status}")
            links = item.setdefault("evidence", [])
            links += [e for e in evidence if e and e not in links]
            item["title"] = title or item.get("title", "")
            item["proposal"] = proposal
            item.pop("draft_proposal", None)
            item["status"] = "proposed"
            item["proposed_at"] = today
            break
    else:
        links = [e for e in dict.fromkeys(evidence) if e]
        if not links:
            raise ValueError("a new proposal needs at least one evidence link")
        items.append({"id": item_id, "title": title, "evidence": links, "seen_count": len(links),
                      "first_seen": today, "last_seen": today, "status": "proposed",
                      "proposal": proposal, "proposed_at": today})
    return _write(path, items, f"propose {item_id}")


def plan_status(home: str, item_id: str, status: str, today: str, aligned_with: str = "", note: str = "") -> list[dict]:
    """Plan initiatives.json with one status change. Only one item may be active, and only after manager alignment."""
    path = career_state.paths(home)["initiatives"]
    items = _items(home)
    item = next((i for i in items if isinstance(i, dict) and i.get("id") == item_id), None)
    if item is None:
        raise ValueError(f"no initiative with id {item_id}")
    current = item.get("status")
    if (current, status) not in MOVES:
        raise ValueError(f"cannot move {item_id} from {current} to {status}")
    if status == "active":
        other = next((i for i in items if isinstance(i, dict) and i.get("status") == "active"), None)
        if other is not None:
            raise ValueError(f"{other.get('id')} is already active; finish or drop it first")
        aligned_with = aligned_with.strip()
        if not aligned_with:
            raise ValueError("an initiative becomes active only after manager alignment: pass who agreed")
        item["aligned"] = {"with": aligned_with, "on": today, "note": note}
    item["status"] = status
    item[f"{status}_at"] = today
    if note and status != "active":
        item[f"{status}_note"] = note
    return _write(path, items, f"move {item_id} to {status}")


def plan_run(home: str, today: str) -> list[dict]:
    """Plan opportunity-state.json with this run's date."""
    path = career_state.paths(home)["opportunity_state"]
    state = _load_json(Path(path))
    state = state if isinstance(state, dict) else {}
    state["last_run"] = today
    return _write(path, state, "record this opportunity scan")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only helper for opportunity-scan.")
    parser.add_argument("command", choices=["context", "propose", "status", "run"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", required=True)
    parser.add_argument("--id")
    parser.add_argument("--title", default="")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--proposal", help="the proposal fields as a JSON object")
    parser.add_argument("--status")
    parser.add_argument("--aligned-with", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    try:
        if args.command == "context":
            result: object = context(args.home, args.today)
        elif args.command == "run":
            result = plan_run(args.home, args.today)
        elif args.command == "propose":
            if not (args.id and args.proposal):
                parser.error("propose needs --id and --proposal")
            try:
                proposal = json.loads(args.proposal)
            except json.JSONDecodeError as exc:
                parser.error(f"--proposal is not valid JSON: {exc}")
            if not isinstance(proposal, dict):
                parser.error("--proposal must be a JSON object")
            result = plan_propose(args.home, args.id, args.title, args.evidence, proposal, args.today)
        else:
            if not (args.id and args.status):
                parser.error("status needs --id and --status")
            result = plan_status(args.home, args.id, args.status, args.today, args.aligned_with, args.note)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
