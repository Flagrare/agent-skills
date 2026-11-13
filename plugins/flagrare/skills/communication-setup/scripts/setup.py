#!/usr/bin/env python3
"""Install, remove or report the communication setup in ~/.claude.

  setup.py install <config.json>   write the output style, copy both hooks, register them in settings.json
  setup.py remove                  undo all of it and restore the output style the user had before
  setup.py status                  print what is installed

Everything it adds to settings.json points into ~/.claude/hooks/communication-setup/, which is how
remove finds its own entries and leaves the user's other hooks alone. settings.json is backed up to
settings.json.bak before every change. --home overrides ~ (for tests).
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "/hooks/communication-setup/"
HOOKS = {"Stop": "reply_length.py", "UserPromptSubmit": "reply_reminder.py"}


def paths(home):
    claude = os.path.join(home, ".claude")
    return {
        "claude": claude,
        "settings": os.path.join(claude, "settings.json"),
        "config": os.path.join(claude, "communication-setup.json"),
        "state": os.path.join(claude, "communication-setup.state.json"),
        "hooks": os.path.join(claude, "hooks", "communication-setup"),
        "styles": os.path.join(claude, "output-styles"),
    }


def read_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    with open(tmp) as f:
        json.load(f)  # never leave a broken settings file behind
    os.replace(tmp, path)


def style_markdown(config):
    lines = ["---", f"name: {config['style_name']}",
             f"description: {config.get('description', 'Short, answer-first replies in plain words.')}",
             "keep-coding-instructions: true", "---", "", f"# How to talk to {config.get('name', 'the user')}", ""]
    if config.get("about"):
        lines += [config["about"], ""]
    lines += ["## Rules", ""] + [f"- {r}" for r in config.get("rules", [])] + [""]
    if config.get("draft_rules"):
        lines += ["## Drafts", "", f"Text {config.get('name', 'the user')} will send under their own name (PR replies, "
                  "Slack, comments) follows these from the first draft, not after a correction:", ""]
        lines += [f"- {r}" for r in config["draft_rules"]] + [""]
    lines += [f"Replies stay within about {config.get('max_lines', 8)} lines and {config.get('max_words', 120)} "
              "words outside `>` quoted drafts. A reply a little over gets a quiet note on the next message; one far over "
              "is blocked once. Neither applies when the user asked for depth "
              f"({', '.join(config.get('depth_words', [])[:6]) or 'explain, details, full'}). Even then, the "
              "answer comes first.", ""]
    if config.get("example_bad") and config.get("example_good"):
        lines += ["## Example", "", "Bad:"] + [f"> {l}" for l in config["example_bad"].splitlines()]
        lines += ["", "Good:"] + [f"> {l}" for l in config["example_good"].splitlines()] + [""]
    return "\n".join(lines)


def strip_ours(settings):
    hooks = settings.get("hooks", {})
    for event in list(hooks):
        kept = []
        for group in hooks[event]:
            group["hooks"] = [h for h in group.get("hooks", []) if MARK not in h.get("command", "")]
            if group["hooks"]:
                kept.append(group)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not hooks:
        settings.pop("hooks", None)


def backup(p):
    if os.path.exists(p["settings"]):
        shutil.copy2(p["settings"], p["settings"] + ".bak")


def install(p, config_path):
    config = read_json(config_path, None)
    if not config or not config.get("style_name") or not config.get("rules"):
        sys.exit("config needs at least style_name and rules")
    previous = read_json(p["config"], {})
    settings = read_json(p["settings"], {})
    backup(p)
    # Keep the style the user had before the first install, so remove can put it back.
    if "previous_output_style" in previous:
        config["previous_output_style"] = previous["previous_output_style"]
    else:
        config["previous_output_style"] = settings.get("outputStyle")
    old_style = previous.get("style_name")
    if old_style and old_style != config["style_name"]:
        old_file = os.path.join(p["styles"], f"{old_style}.md")
        if os.path.exists(old_file):
            os.remove(old_file)

    os.makedirs(p["hooks"], exist_ok=True)
    for script in HOOKS.values():
        shutil.copy2(os.path.join(HERE, script), os.path.join(p["hooks"], script))
    os.makedirs(p["styles"], exist_ok=True)
    with open(os.path.join(p["styles"], f"{config['style_name']}.md"), "w") as f:
        f.write(style_markdown(config))
    write_json(p["config"], config)

    strip_ours(settings)
    hooks = settings.setdefault("hooks", {})
    for event, script in HOOKS.items():
        hooks.setdefault(event, []).append({"hooks": [{
            "type": "command", "command": f"python3 {os.path.join(p['hooks'], script)}", "timeout": 10}]})
    settings["outputStyle"] = config["style_name"]
    write_json(p["settings"], settings)
    print(f"installed: output style '{config['style_name']}', Stop length check, per-message reminder")


def remove(p):
    config = read_json(p["config"], {})
    settings = read_json(p["settings"], {})
    backup(p)
    strip_ours(settings)
    if config.get("style_name") and settings.get("outputStyle") == config["style_name"]:
        if config.get("previous_output_style"):
            settings["outputStyle"] = config["previous_output_style"]
        else:
            settings.pop("outputStyle", None)
    write_json(p["settings"], settings)
    if config.get("style_name"):
        style = os.path.join(p["styles"], f"{config['style_name']}.md")
        if os.path.exists(style):
            os.remove(style)
    shutil.rmtree(p["hooks"], ignore_errors=True)
    for leftover in (p["config"], p["state"]):
        if os.path.exists(leftover):
            os.remove(leftover)
    print("removed: output style, hooks and config; settings.json.bak has the previous settings")


def status(p):
    config = read_json(p["config"], None)
    settings = read_json(p["settings"], {})
    ours = [e for e, groups in settings.get("hooks", {}).items()
            for g in groups for h in g.get("hooks", []) if MARK in h.get("command", "")]
    print(json.dumps({
        "installed": bool(config),
        "style": config.get("style_name") if config else None,
        "style_active": bool(config) and settings.get("outputStyle") == config.get("style_name"),
        "hooks": sorted(ours),
        "max_lines": config.get("max_lines") if config else None,
        "max_words": config.get("max_words") if config else None,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["install", "remove", "status"])
    parser.add_argument("config", nargs="?")
    parser.add_argument("--home", default=os.path.expanduser("~"))
    args = parser.parse_args()
    p = paths(args.home)
    if args.command == "install":
        if not args.config:
            sys.exit("install needs a config file")
        install(p, args.config)
    elif args.command == "remove":
        remove(p)
    else:
        status(p)


if __name__ == "__main__":
    main()
