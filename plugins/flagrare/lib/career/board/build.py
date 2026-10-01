#!/usr/bin/env python3
"""Render the career board.

Usage: python3 build.py <board_dir> [--home HOME] [--today YYYY-MM-DD]

Reads <board_dir>/data.json, the contributions log (the union of the career
and legacy senior-scan logs), and, through coordinator.board, the active and
proposed initiatives, the promotion map summary and evidence per rubric row.
Embeds all of it into template.html (next to this script) and writes
<board_dir>/board.html. The board folder is the user's own; this is the only
file the library writes.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import career_state  # noqa: E402
import coordinator  # noqa: E402

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%232c5b87'/%3E"
        "%3Ccircle cx='16' cy='16' r='10' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='5' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='1.8' fill='%23f0b35c'/%3E%3C/svg%3E")
ENTRY = re.compile(r"- (\d{4}-\d{2}-\d{2}) \| (\S+) \| (.+?) \| behavior: (.+?)(?: \| row: (\S+))?$")


def link_title(link: str) -> str:
    pr = re.search(r"github\.com/[^/]+/([^/]+)/pull/(\d+)", link)
    if pr:
        return f"{pr.group(1)} #{pr.group(2)}"
    ticket = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", link)
    if ticket:
        return ticket.group(1)
    if "slack.com" in link:
        return "Slack thread"
    if "notion." in link:
        return "Notion page"
    return "Link"


def parse_contributions(lines: list[str]) -> list[dict]:
    """Log entries as board records. The trailing `| row: <id>` field is optional."""
    out = []
    for i, line in enumerate(lines):
        m = ENTRY.match(line.strip())
        if m:
            date, link, what, behavior, row = m.groups()
            out.append({"id": f"c{i}", "date": date, "link": link, "title": link_title(link),
                        "what": what, "behavior": behavior, "row": row})
    return out


def render(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    body = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda _: "/*DATA*/" + payload + "/*END*/", template, flags=re.S)
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<link rel="icon" type="image/svg+xml" href="{html.escape(ICON)}">'
            '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
            '</head><body>' + body + '</body></html>')


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the career board.")
    parser.add_argument("board_dir")
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", help="defaults to the scan date in data.json, then today")
    args = parser.parse_args()
    board = Path(args.board_dir).expanduser()
    data = json.loads((board / "data.json").read_text(encoding="utf-8"))
    data["contributions"] = parse_contributions(career_state.read_contributions(args.home))
    today = args.today or (data.get("scan") or {}).get("date") or datetime.date.today().isoformat()
    data["career"] = coordinator.board(args.home, today)
    out = board / "board.html"
    out.write_text(render(data), encoding="utf-8")
    print(f"wrote {out}: {len(data.get('items', []))} items, {len(data['contributions'])} contributions")


if __name__ == "__main__":
    main()
