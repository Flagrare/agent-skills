#!/usr/bin/env python3
"""Reminder hooks for /flagrare:measure-impact.

`session-start` (SessionStart): one line for the user when measurements are due.
`moment` (PostToolUse): a short note for Claude when a measurable moment happens.
Neither may ever break a session: any error means no output and exit 0.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib" / "career"
OFF_VALUES = (False, "false", "off", "no", "0", 0)


def _lib():
    """The career library, imported lazily so a broken library can never break a tool call."""
    if str(LIB) not in sys.path:
        sys.path.insert(0, str(LIB))
    import career_state
    import measurements
    return career_state, measurements


def reminders_on(home: str) -> bool:
    career_state, _ = _lib()
    try:
        config = json.loads(Path(career_state.paths(home)["config"]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    block = ((config.get("skills") or {}).get("measure-impact") or {}) if isinstance(config, dict) else {}
    value = block.get("reminders", True)
    return (value.strip().lower() if isinstance(value, str) else value) not in OFF_VALUES


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def session_start(home: str, today: str) -> dict | None:
    if not reminders_on(home):
        return None
    _, measurements = _lib()
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
        for segment in SEGMENT_RE.split(command):
            words = segment.strip().split()
            if words[:3] in (["gh", "pr", "merge"], ["gh", "pr", "create"]) and not {"--help", "-h", "--auto"} & set(words):
                if words[2] == "merge":
                    return f"merge:{segment.strip()[:120]}", "a PR was merged", "launch"
                return f"create:{segment.strip()[:120]}", "a PR was opened", "before"
        if LOG_APPEND_RE.search(command):
            return f"log:{_digest(command)}", "a contribution was logged", "past"
    if tool in ("Write", "Edit") and str(data.get("file_path", "")).endswith("career/contributions.log.md"):
        return f"log:{_digest(json.dumps(data, sort_keys=True))}", "a contribution was logged", "past"
    return None


SEGMENT_RE = re.compile(r"&&|\|\||;|\||\n")
LOG_APPEND_RE = re.compile(
    r"(>>|tee\s+-a)[^;&|\n]*contributions\.log\.md"
    r"|open\([^)]*contributions\.log\.md[^)]*,\s*['\"]a['\"]",
)


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _saved(home: str) -> list[dict]:
    _, measurements = _lib()
    try:
        return [i for i in measurements.load(home) if isinstance(i, dict)]
    except (measurements.CorruptFile, ValueError):
        return []


def _mentions(token: str, text: str) -> bool:
    return bool(token) and re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text) is not None


def _skipped(event: dict, items: list[dict]) -> bool:
    text = json.dumps(event.get("tool_input") or {}, ensure_ascii=False)
    for item in items:
        if item.get("stage") == "skipped":
            link = (item.get("work") or {}).get("link") or ""
            last = link.rstrip("/").rsplit("/", 1)[-1] if link else ""
            if (link and link in text) or (len(last) > 2 and _mentions(last, text)) or (len(str(item.get("id", ""))) > 3 and _mentions(str(item["id"]), text)):
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
    items = _saved(home)
    if _skipped(event, items) or not _first_time(str(event.get("session_id") or ""), key, state_dir):
        return None
    if stage == "launch":
        waiting = [f"{(i.get('work') or {}).get('title', '')} ({i.get('id')})" for i in items
                   if i.get("stage") == "before" and not i.get("launch_date")][:3]
        named = f" Saved measurements still waiting for a launch date: {'; '.join(waiting)}." if waiting else ""
        ask = ("ask the user when this work reaches users and run /flagrare:measure-impact to record the launch date, "
               "so the 2- and 6-week checks come due on their own; if it has no saved measurement, offer to set one up" + named)
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
        elif mode == "expansion":
            event = json.loads(stdin_text) if stdin_text.strip() else {}
            if not isinstance(event, dict):
                return ""
            name = str(event.get("command_name") or "")
            args = event.get("command_args")
            skill_event = {"session_id": event.get("session_id"), "tool_name": "Skill",
                           "tool_input": {"skill": name if ":" in name else f"flagrare:{name}",
                                          "args": " ".join(map(str, args)) if isinstance(args, list) else str(args or "")}}
            out = moment(skill_event, home, str(event.get("scratchpad_dir") or state_dir))
            return out["hookSpecificOutput"]["additionalContext"] if out else ""
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
