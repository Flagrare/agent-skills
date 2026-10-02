#!/usr/bin/env python3
"""Reminder hooks for /flagrare:measure-impact.

`session-start` (SessionStart): one line for the user when measurements are due.
`moment` (PostToolUse): a short note for Claude when a measurable moment happens.
Neither may ever break a session: any error means no output and exit 0.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib" / "career"))

import career_state  # noqa: E402
import measurements  # noqa: E402


def reminders_on(home: str) -> bool:
    try:
        config = json.loads(Path(career_state.paths(home)["config"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    block = ((config.get("skills") or {}).get("measure-impact") or {}) if isinstance(config, dict) else {}
    return block.get("reminders", True) is not False


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def session_start(home: str, today: str) -> dict | None:
    if not reminders_on(home):
        return None
    try:
        due = measurements.due(home, today)
    except measurements.CorruptFile as exc:
        return {"systemMessage": f"Impact: {exc}"}
    if not due["count"]:
        return None
    parts = []
    checks = due["checks_due"]
    if checks:
        more = ", and more" if len(checks) > 1 else ""
        parts.append(f"{_plural(len(checks), 'check')} due ({checks[0]['title']}{more})")
    if due["bets_waiting"]:
        parts.append(f"{_plural(len(due['bets_waiting']), 'bet')} waiting for a launch date")
    if due["unmeasured_wins"]:
        parts.append(f"{_plural(len(due['unmeasured_wins']), 'recent win')} with no number")
    pronoun = "it" if due["count"] == 1 else "them"
    line = f"Impact: {', '.join(parts)}. Ask Claude to measure {pronoun} when you have a minute."
    context = ("measure-impact items due (from measurements.py due): " + json.dumps(due, ensure_ascii=False)
               + ". Mention them once, at a natural point; never interrupt the user's current task for them.")
    return {"systemMessage": line, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}
