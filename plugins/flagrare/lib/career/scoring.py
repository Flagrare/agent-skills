"""Inputs for impact-scan's Stretch and Audience axes. Read-only.

The model still judges which open rubric row an item closes and who will see
it; this module only lists the choices, from the promotion map when there is
one, or from the scan's own config when there isn't.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import career_state


def open_rows(m: dict) -> list[dict]:
    """Rubric rows not yet done, as {id, area, target_text}. Empty when the map has no rubric."""
    rows = (m.get("rubric") or {}).get("rows") or []
    result = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") == "done" or not row.get("id"):
            continue
        target = row.get("target_text")
        if isinstance(target, dict):
            target = target.get("value")
        result.append({"id": row["id"], "area": row.get("area", ""), "target_text": target or ""})
    return result


def unseen_people(m: dict) -> list[str]:
    """Names of people in the map who have not seen the user's work."""
    people = m.get("people") or []
    return [p["name"] for p in people if isinstance(p, dict) and p.get("name") and p.get("seen_your_work") is False]


def context(home: str) -> dict:
    """What impact-scan scores against: the map's open rows and unseen people, plus the config fallback."""
    p = career_state.paths(home)
    try:
        config = json.loads(Path(p["config"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}
    scan = career_state.skill_config(config, "impact-scan")
    fallback = {"target_behaviors": scan.get("target_behaviors", []), "audience": scan.get("audience", [])}
    try:
        m = json.loads(Path(p["map_json"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        m = None
    if not isinstance(m, dict):
        return {"has_map": False, "open_rows": [], "unseen_people": [], "fallback": fallback}
    return {"has_map": True, "open_rows": open_rows(m), "unseen_people": unseen_people(m), "fallback": fallback}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scoring inputs for impact-scan.")
    parser.add_argument("command", choices=["context"])
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    print(json.dumps(context(args.home), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
