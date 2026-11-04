#!/usr/bin/env python3
"""Stop hook: block a reply that runs longer than the user asked for, and ask Claude to rewrite it.

Installed by /flagrare:communication-setup. Settings come from ~/.claude/communication-setup.json.

What counts is prose outside `>` quoted drafts and ``` code blocks: drafts are what the user will send,
so their length is the user's call. A long reply is blocked once; the rewrite passes with a warning
(stop_hook_active), so it never loops. When the user's last message asks for depth ("explain",
"full", "details"...), any length passes.
"""
import json
import os
import re
import sys

CONFIG = os.path.join(os.path.expanduser("~"), ".claude", "communication-setup.json")
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
    lines = prose(data.get("last_assistant_message") or "")
    words = sum(len(line.split()) for line in lines)
    if len(lines) <= max_lines and words <= max_words:
        return
    if asks_for_depth(last_user_prompt(data.get("transcript_path")), config.get("depth_words", DEFAULT_DEPTH_WORDS)):
        return
    if data.get("stop_hook_active"):
        print(json.dumps({"systemMessage": "communication-setup: the reply is still long."}))
        return
    who = config.get("name") or "the user"
    print(json.dumps({"decision": "block", "reason":
        f"Reply too long for {who} ({len(lines)} lines, {words} words outside drafts; the limit is "
        f"{max_lines} lines and {max_words} words). Rewrite it: the answer first in one or two lines, no "
        "narration of what you checked or ran, no caveats nobody asked for, plain words, at most one "
        "question at the end. Keep any `>` drafts as they are. Resend the whole reply."}))


if __name__ == "__main__":
    main()
