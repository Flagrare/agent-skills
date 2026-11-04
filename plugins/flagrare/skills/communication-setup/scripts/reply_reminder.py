#!/usr/bin/env python3
"""UserPromptSubmit hook: put the user's reply rules next to every message they send, plus a quiet note
when the last reply ran a little long.

Installed by /flagrare:communication-setup. The rules come from ~/.claude/communication-setup.json,
so they never fall out of view in a long session.
"""
import json
import os

CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.json")
STATE = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.state.json")

try:
    with open(CONFIG) as f:
        config = json.load(f)
except (OSError, ValueError):
    config = {}

# reply_length.py leaves this when the last reply ran a little long; nudge once, then forget it.
try:
    with open(STATE) as f:
        overrun = json.load(f)
    os.remove(STATE)
except (OSError, ValueError):
    overrun = None

rules = config.get("rules") or []
if rules:
    who = config.get("name") or "the user"
    text = f"Reply rules for {who}: " + " ".join(f"{i}) {r}" for i, r in enumerate(rules, 1))
    if overrun:
        text += (f" Your last reply ran long ({overrun.get('lines')} lines, {overrun.get('words')} words; "
                 f"the limit is {config.get('max_lines', 8)} lines and {config.get('max_words', 120)} words). "
                 "Keep this one shorter.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))
