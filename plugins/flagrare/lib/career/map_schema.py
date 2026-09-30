"""Checks for promotion-map.json. Read-only; reports, never fixes."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

SECTIONS = ["target", "process", "calendar", "rubric", "org", "people", "precedent", "packet_readiness", "manager_questions"]
STATUSES = {"verified", "unverified", "inferred"}


def _walk(node: object, path: str):
    if isinstance(node, dict):
        if "status" in node:
            yield path, node
            for i, alt in enumerate(node.get("alternatives", []) or []):
                yield from _walk(alt, f"{path}.alternatives[{i}]")
            return
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def validate(m: dict) -> list[str]:
    errors: list[str] = []
    for section in SECTIONS:
        if section not in m:
            continue
        for path, fact in _walk(m[section], section):
            if fact.get("status") not in STATUSES:
                errors.append(f"{path}: status must be one of {sorted(STATUSES)}")
            if "alternatives" in fact:
                if len(fact["alternatives"]) < 2:
                    errors.append(f"{path}: alternatives needs at least two entries")
                continue
            for field in ("value", "source", "checked_at"):
                if field not in fact:
                    errors.append(f"{path}: missing {field}")
    return errors


def conflicts(m: dict) -> list[str]:
    found: list[str] = []
    for section in SECTIONS:
        if section in m:
            found += [path for path, fact in _walk(m[section], section) if "alternatives" in fact]
    return found


def missing_sections(m: dict) -> list[str]:
    return [s for s in SECTIONS if s not in m]


def stale_sections(m: dict, today: date, days: int = 90) -> list[str]:
    meta = m.get("sections", {})
    stale: list[str] = []
    for section in SECTIONS:
        if section not in m:
            continue
        checked = meta.get(section, {}).get("checked_at")
        if not checked or (today - date.fromisoformat(checked)).days > days:
            stale.append(section)
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a promotion-map.json file.")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("map_path")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()
    m = json.loads(Path(args.map_path).read_text(encoding="utf-8"))
    today = date.fromisoformat(args.today)
    print(json.dumps({
        "errors": validate(m),
        "missing": missing_sections(m),
        "stale": stale_sections(m, today),
        "conflicts": conflicts(m),
    }, indent=2))


if __name__ == "__main__":
    main()
