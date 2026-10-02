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


MOMENT_SKILLS = {
    "flagrare:tdd-writer": ("a TDD is being written", "before"),
    "flagrare:work-prep": ("a ticket is being picked up", "before"),
    "flagrare:intake": ("a ticket is being picked up", "before"),
    "flagrare:opportunity-scan": ("projects are being proposed", "before"),
    "flagrare:open-pr": ("a PR is being opened", "before"),
    "flagrare:release-check": ("a release is being checked", "launch"),
}


def moment_of(event: dict) -> tuple[str, str, str] | None:
    tool = event.get("tool_name")
    data = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    if tool == "Skill" and data.get("skill") in MOMENT_SKILLS:
        what, stage = MOMENT_SKILLS[data["skill"]]
        return f"skill:{data['skill']}:{str(data.get('args', ''))[:120]}", what, stage
    if tool == "Bash":
        command = str(data.get("command", ""))
        if "gh pr merge" in command:
            return f"merge:{command[:120]}", "a PR was merged", "launch"
        if "gh pr create" in command:
            return f"create:{command[:120]}", "a PR was opened", "before"
        if "contributions.log.md" in command:
            return "log", "a contribution was logged", "past"
    if tool in ("Write", "Edit") and str(data.get("file_path", "")).endswith("career/contributions.log.md"):
        return "log", "a contribution was logged", "past"
    return None


def _skipped(event: dict, home: str) -> bool:
    try:
        items = measurements.load(home)
    except measurements.CorruptFile:
        return False
    text = json.dumps(event.get("tool_input") or {}, ensure_ascii=False)
    for item in items:
        if isinstance(item, dict) and item.get("stage") == "skipped":
            link = (item.get("work") or {}).get("link") or ""
            last = link.rstrip("/").rsplit("/", 1)[-1] if link else ""
            if (link and link in text) or (len(last) > 2 and last in text) or (len(str(item.get("id", ""))) > 3 and str(item["id"]) in text):
                return True
    return False


def _first_time(session_id: str, key: str, state_dir: str) -> bool:
    if not session_id:
        return True
    path = Path(state_dir) / f"flagrare-measure-{session_id}.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8"))
        seen = seen if isinstance(seen, list) else []
    except (OSError, json.JSONDecodeError):
        seen = []
    if key in seen:
        return False
    try:
        path.write_text(json.dumps(seen + [key]), encoding="utf-8")
    except OSError:
        pass
    return True


def moment(event: dict, home: str, state_dir: str) -> dict | None:
    if not isinstance(event, dict):
        return None
    found = moment_of(event)
    if not found or not reminders_on(home):
        return None
    key, what, stage = found
    if _skipped(event, home) or not _first_time(str(event.get("session_id") or ""), key, state_dir):
        return None
    if stage == "launch":
        ask = ("if this work has a saved measurement, ask the user when it reaches users and record that date with "
               "measurements.py launch, so the checks come due on their own; if it has none, offer /flagrare:measure-impact (before stage)")
    else:
        ask = f"offer /flagrare:measure-impact ({stage} stage)"
    note = (f"Measure-impact moment: {what}. Unless this is a small fix, the user already measured or skipped this work, "
            f"or this is a scheduled run, {ask} in one short line at the end of your reply. "
            "Do not interrupt the current task for it, and do not offer it again for this work in this session.")
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}


def main(argv: list[str], stdin_text: str, home: str, today: str, state_dir: str) -> str:
    mode = argv[1] if len(argv) > 1 else ""
    try:
        if mode == "session-start":
            out = session_start(home, today)
        elif mode == "moment":
            event = json.loads(stdin_text) if stdin_text.strip() else {}
            if isinstance(event, dict):
                out = moment(event, home, str(event.get("scratchpad_dir") or state_dir))
            else:
                out = None
        else:
            out = None
    except Exception:  # a reminder must never break the session
        return ""
    return json.dumps(out, ensure_ascii=False) if out else ""


if __name__ == "__main__":
    try:
        text = sys.stdin.read()
    except Exception:
        text = ""
    printed = main(sys.argv, text, os.path.expanduser("~"), date.today().isoformat(), tempfile.gettempdir())
    if printed:
        print(printed)
    sys.exit(0)
