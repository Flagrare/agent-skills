#!/usr/bin/env python3
"""Stop hook: keep replies within the user's limit without making the conversation jarring.

Installed by /flagrare:communication-setup. Settings come from ~/.claude/communication-setup.json.

What counts is prose outside `>` quoted drafts and ``` code blocks: drafts are what the user will send,
so their length is the user's call. Two tiers, because a block shows the user the long reply, a hook
message and then a rewrite:
- A little over the limit (up to hard_factor times it): no block. The overrun is saved to the state
  file, and reply_reminder.py adds a quiet note to the next message, so the user sees nothing.
- Far over: blocked once with a one-line reason. The rewrite passes (stop_hook_active), so it never loops.
When the user's last message asks for depth ("explain", "full", "details"...), any length passes.
"""
import json
import os
import re
import sys

CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.json")
STATE = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.state.json")
DEFAULT_DEPTH_WORDS = ["explain", "detail", "details", "full", "everything", "elaborate", "in depth",
                       "deep dive", "write up", "writeup", "step by step", "walk me through", "list all"]


def load_config():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def prose(text):
    out, in_code = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith(">"):
            continue
        out.append(s)
    return out


def last_user_prompt(path):
    try:
        with open(path) as f:
            lines = f.readlines()
    except (OSError, TypeError):
        return ""
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") != "user":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
            if texts:
                return "\n".join(texts)
    return ""


def asks_for_depth(prompt, words):
    # Tagged blocks (system notices, hook feedback, pasted content) aren't the user asking for depth.
    prompt = re.sub(r"<([\w-]+)[^>]*>.*?</\1>", "", prompt, flags=re.S)
    pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
    return bool(words) and re.search(pattern, prompt, re.I) is not None


def main():
    data = json.load(sys.stdin)
    config = load_config()
    max_lines = config.get("max_lines", 8)
    max_words = config.get("max_words", 120)
    hard = config.get("hard_factor", 2)
    lines = prose(data.get("last_assistant_message") or "")
    words = sum(len(line.split()) for line in lines)
    if len(lines) <= max_lines and words <= max_words:
        return
    if asks_for_depth(last_user_prompt(data.get("transcript_path")), config.get("depth_words", DEFAULT_DEPTH_WORDS)):
        return
    if data.get("stop_hook_active"):
        return
    if len(lines) <= max_lines * hard and words <= max_words * hard:
        with open(STATE, "w") as f:
            json.dump({"lines": len(lines), "words": words}, f)
        return
    print(json.dumps({"decision": "block", "reason":
        f"Too long ({len(lines)} lines, limit {max_lines}). Resend it short: answer first, no process, "
        "one question at the end. Keep any `>` drafts as they are."}))


if __name__ == "__main__":
    main()
