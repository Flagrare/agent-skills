#!/usr/bin/env python3
"""UserPromptSubmit hook: put the user's reply rules next to every message they send.

Installed by /flagrare:communication-setup. The rules come from ~/.claude/communication-setup.json,
so they never fall out of view in a long session.
"""
import json
import os

CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.json")

try:
    with open(CONFIG) as f:
        config = json.load(f)
except (OSError, ValueError):
    config = {}

rules = config.get("rules") or []
if rules:
    who = config.get("name") or "the user"
    text = f"Reply rules for {who}: " + " ".join(f"{i}) {r}" for i, r in enumerate(rules, 1))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))
