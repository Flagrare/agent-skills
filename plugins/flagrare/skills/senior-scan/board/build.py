#!/usr/bin/env python3
"""Render the Senior Scan Board.

Usage: python3 build.py <board_dir>

Reads <board_dir>/data.json and the contributions log, embeds both into
template.html (next to this script), and writes <board_dir>/board.html.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.expanduser("~/.claude/skills/flagrare/senior-scan/contributions.log.md")
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%232c5b87'/%3E"
        "%3Ccircle cx='16' cy='16' r='10' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='5' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='1.8' fill='%23f0b35c'/%3E%3C/svg%3E")


def link_title(link):
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


def contributions():
    if not os.path.exists(LOG):
        return []
    out = []
    for i, line in enumerate(open(LOG)):
        m = re.match(r"- (\d{4}-\d{2}-\d{2}) \| (\S+) \| (.+?) \| behavior: (.+)$", line.strip())
        if m:
            date, link, what, behavior = m.groups()
            out.append({"id": f"c{i}", "date": date, "link": link, "title": link_title(link),
                        "what": what, "behavior": behavior})
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: build.py <board_dir>")
    board_dir = os.path.expanduser(sys.argv[1])
    data = json.load(open(os.path.join(board_dir, "data.json")))
    data["contributions"] = contributions()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = open(os.path.join(HERE, "template.html")).read()
    body = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda _: "/*DATA*/" + payload + "/*END*/", template, flags=re.S)
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
           f'<link rel="icon" type="image/svg+xml" href="{html.escape(ICON)}">'
           '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
           '</head><body>' + body + '</body></html>')
    out = os.path.join(board_dir, "board.html")
    open(out, "w").write(doc)
    print(f"wrote {out}: {len(data.get('items', []))} items, {len(data['contributions'])} contributions")


if __name__ == "__main__":
    main()
