"""The user's own work as project streams, for the evidence log. Never writes files.

The impact scan hunts other people's threads and skips the user's own PRs and
posts, so without this the log only ever held replies. The skill gathers the
user's own items (authored PRs, docs they drive, tickets, meetings and threads
that discuss them) into one shape, this module groups them into projects, and
plans the log line and own-work.json content the skill writes with the Write
tool. The skill still writes each project's story; this module only keeps the
bookkeeping honest: one entry per project, later work joins the same project,
and a new entry only at a milestone.

Item shape: {source, link, title, date, keys: [ticket keys], links: [links it mentions]}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import career_state

KEY = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d+\b")
TITLE_SOURCES = ("notion", "jira", "confluence", "docs")


def _load(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load(home: str) -> dict:
    """own-work.json, or an empty state."""
    data = _load(Path(career_state.paths(home)["own_work"]))
    if not isinstance(data, dict):
        data = {}
    streams = [s for s in (data.get("streams") or []) if isinstance(s, dict) and s.get("id")]
    return {"last_harvest": data.get("last_harvest"), "streams": streams}


def own_links(home: str) -> set[str]:
    """Every link that belongs to one of the user's own projects."""
    out: set[str] = set()
    for s in load(home)["streams"]:
        out.update(s.get("links") or [])
        out.update(s.get("log_links") or [])
    return out


def stream_of(home: str, link: str) -> dict | None:
    return next((s for s in load(home)["streams"] if link in (s.get("links") or []) or link in (s.get("log_links") or [])), None)


def _write(path: str, content: str, reason: str) -> dict:
    return {"action": "write", "path": path, "content": content, "reason": reason}


def _json(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _keys(item: dict) -> set[str]:
    keys = {k for k in (item.get("keys") or []) if isinstance(k, str)}
    return keys | set(KEY.findall(str(item.get("title") or "")))


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "project"


def group(home: str, items: list[dict], today: str) -> list[dict]:
    """Proposed streams for the items not logged yet. Items that share a ticket key or mention each other's
    links are one project; an item that touches a known stream joins it. Known links alone propose nothing."""
    items = [i for i in items if isinstance(i, dict) and i.get("link")]
    streams = load(home)["streams"]
    n = len(items)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    by_key: dict[str, int] = {}
    by_link = {item["link"]: i for i, item in enumerate(items)}
    for i, item in enumerate(items):
        for k in _keys(item):
            if k in by_key:
                union(i, by_key[k])
            else:
                by_key[k] = i
        for link in item.get("links") or []:
            if link in by_link:
                union(i, by_link[link])

    groups: dict[int, list[dict]] = {}
    for i, item in enumerate(items):
        groups.setdefault(find(i), []).append(item)

    out = []
    for members in groups.values():
        members = sorted(members, key=lambda m: str(m.get("date") or ""))
        keys = set().union(*(_keys(m) for m in members))
        links = {m["link"] for m in members} | {l for m in members for l in (m.get("links") or [])}
        known = next((s for s in streams if keys & set(s.get("keys") or []) or links & set(s.get("links") or [])), None)
        new_links = [m["link"] for m in members if not known or m["link"] not in (known.get("links") or [])]
        if not new_links:
            continue
        titled = next((m for m in members if m.get("source") in TITLE_SOURCES), members[0])
        counts: dict[str, int] = {}
        for m in members:
            for k in _keys(m):
                counts[k] = counts.get(k, 0) + 1
        # The key most members share is the project's (usually its epic); ties go to the lowest key.
        common = min(counts, key=lambda k: (-counts[k], k)) if counts else ""
        out.append({
            "id": known["id"] if known else _slug(common or str(titled.get("title") or "")),
            "known": bool(known),
            "already_logged": bool(known and known.get("log_links")),
            "title_hint": known.get("title") if known else titled.get("title"),
            "keys": sorted(keys),
            "first_date": members[0].get("date"),
            "last_date": members[-1].get("date"),
            "members": members,
            "new_links": new_links,
        })
    return sorted(out, key=lambda s: str(s["first_date"] or ""))


def log_line(today: str, link: str, what: str, behavior: str, row: str = "") -> str:
    """One log entry in the exact shape every reader parses; refuses anything that would break it."""
    for name, value in (("link", link), ("what", what), ("behavior", behavior), ("row", row)):
        if "|" in value or "\n" in value:
            raise ValueError(f"{name} can't contain '|' or a line break: it would break the log line")
    if not link or " " in link:
        raise ValueError("link must be one URL")
    if row and " " in row:
        raise ValueError("row must be a rubric row id")
    line = f"- {today} | {link} | {what.strip()} | behavior: {behavior.strip()}" + (f" | row: {row}" if row else "")
    if not career_state.LOG_LINE.match(line):
        raise ValueError(f"not a valid log line: {line}")
    return line


def record(home: str, records: list[dict], today: str) -> list[dict]:
    """Plan the log and own-work.json for a batch of projects, so a run writes the log once.
    A project already in the log gets a new line only when the record is a milestone."""
    p = career_state.paths(home)
    state = load(home)
    streams = {s["id"]: s for s in state["streams"]}
    log_path = Path(p["log"])
    text = log_path.read_text(encoding="utf-8") if log_path.is_file() else "# Contributions\n\n"
    existing = set(career_state.read_contributions(home))
    logged_links = {m.group(2) for m in (career_state.LOG_LINE.match(l.strip()) for l in existing) if m}
    added = []
    for rec in records:
        sid = str(rec.get("stream") or "").strip()
        if not sid:
            raise ValueError("each record needs its stream id")
        members = [m for m in (rec.get("members") or []) if isinstance(m, dict) and m.get("link")]
        stream = streams.get(sid) or {"id": sid, "title": rec.get("title") or sid, "keys": [], "links": [], "log_links": []}
        stream["title"] = rec.get("title") or stream.get("title") or sid
        member_keys: set[str] = set()
        for m in members:
            member_keys |= _keys(m)
        stream["keys"] = sorted(set(stream.get("keys") or []) | member_keys)
        stream["links"] = sorted(set(stream.get("links") or []) | {m["link"] for m in members} | {l for m in members for l in (m.get("links") or [])})
        dates = sorted(str(d) for d in [stream.get("first_date"), stream.get("last_date")] + [m.get("date") for m in members] if d)
        if dates:
            stream["first_date"], stream["last_date"] = dates[0], dates[-1]
        if not stream.get("log_links") and not rec.get("milestone") and rec.get("link") in logged_links:
            # Logged by hand before the project was tracked: it joins the project, no second entry.
            stream["log_links"] = [rec["link"]]
        elif not stream.get("log_links") or rec.get("milestone"):
            line = log_line(str(rec.get("date") or today), str(rec.get("link") or ""), str(rec.get("what") or ""), str(rec.get("behavior") or ""), str(rec.get("row") or ""))
            if line not in existing:
                added.append(line)
                existing.add(line)
                stream["log_links"] = list(dict.fromkeys((stream.get("log_links") or []) + [rec["link"]]))
        streams[sid] = stream
    actions = []
    if added:
        body = text if text.endswith("\n") else text + "\n"
        actions.append(_write(p["log"], body + "\n".join(added) + "\n", f"log {len(added)} project entr{'y' if len(added) == 1 else 'ies'} from your own work"))
    state["streams"] = sorted(streams.values(), key=lambda s: str(s.get("first_date") or ""))
    state["last_harvest"] = today
    actions.append(_write(p["own_work"], _json(state), "record your own projects"))
    return actions


def _item_keys(item: dict) -> set[str]:
    text = " ".join(str(item.get(k) or "") for k in ("action", "context", "link", "title"))
    return set(KEY.findall(text))


def _bare(link: str) -> str:
    """A link without its query and fragment, so a comment link matches its page."""
    return re.split(r"[?#]", str(link), maxsplit=1)[0].rstrip("/")


def _overlap(stream: dict, links: set[str], keys: set[str]) -> bool:
    mine = {_bare(l) for l in (stream.get("links") or []) + (stream.get("log_links") or [])}
    return bool({_bare(l) for l in links if l} & mine or keys & set(stream.get("keys") or []))


def _day(iso: str | None) -> str:
    try:
        y, m, d = str(iso).split("-")
        return f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m) - 1]} {int(d)}"
    except (ValueError, IndexError):
        return str(iso or "")


def reopen(home: str, board: str, today: str) -> list[dict]:
    """Plan the board's data.json. A dropped item the user went on to do (one of their projects shares its link
    or ticket, with work after the item was dropped) is marked done, so it isn't left as "skipped". An open item
    about one of their projects gets a note naming the project, so it isn't read as an unrelated thread.
    A dropped item with no drop date, or no work after it, stays as it is: a shared link alone isn't proof."""
    path = Path(board)
    data = _load(path)
    if not isinstance(data, dict):
        return []
    streams = load(home)["streams"]
    changed = False
    for item in data.get("items") or []:
        status = item.get("status") if isinstance(item, dict) else None
        if status not in ("dropped", "todo", "waiting"):
            continue
        stream = next((s for s in streams if _overlap(s, {str(item.get("link") or "")}, _item_keys(item))), None)
        if stream is None:
            continue
        if status == "dropped":
            dropped_on = str(item.get("dropped_on") or item.get("updated_on") or "")
            if not dropped_on or str(stream.get("last_date") or "") <= dropped_on:
                continue
            item["status"], item["done_on"], item["updated_on"] = "done", today, today
            note = f"You did this: it became your project {stream.get('title')} (from {_day(stream.get('first_date'))})"
        else:
            note = f"Part of your project: {stream.get('title')} (you started it on {_day(stream.get('first_date'))})"
        if item.get("note") != note or item.get("project") != stream["id"]:
            item["note"], item["project"] = note, stream["id"]
            changed = True
    return [_write(str(path), _json(data), "mark done and tag board items about your own projects")] if changed else []


def link_candidates(home: str, today: str) -> list[dict]:
    """Plan initiatives.json: a candidate the user is already building gets `building`. Its status never
    changes here; only the user and their manager make it the project they own."""
    path = career_state.paths(home)["initiatives"]
    items = career_state._load_list(Path(path))
    streams = load(home)["streams"]
    changed = False
    for item in items:
        if not isinstance(item, dict) or item.get("status") not in ("candidate", "proposed", "dropped"):
            continue
        evidence = {str(e) for e in (item.get("evidence") or [])}
        keys = set(KEY.findall(" ".join(evidence | {str(item.get("title") or "")})))
        stream = next((s for s in streams if _overlap(s, evidence, keys)), None)
        if stream is None:
            continue
        building = {"stream": stream["id"], "title": stream.get("title"), "since": stream.get("first_date")}
        if item.get("building") != building:
            item["building"] = building
            changed = True
    return [_write(path, _json(items), "mark candidates you're already building")] if changed else []


def summary(home: str) -> dict:
    """What the board and digest show: the user's projects and the candidates they're already building."""
    streams = load(home)["streams"]
    items = career_state._load_list(Path(career_state.paths(home)["initiatives"]))
    building = [{"id": i.get("id"), "title": i.get("title"), "status": i.get("status"), "building": i["building"]}
                for i in items if isinstance(i, dict) and isinstance(i.get("building"), dict) and i.get("status") != "active"]
    return {"streams": [{"id": s["id"], "title": s.get("title"), "first_date": s.get("first_date"),
                         "last_date": s.get("last_date"), "logged": bool(s.get("log_links"))} for s in streams],
            "building_candidates": building}


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only helper: the user's own work as projects in the evidence log.")
    parser.add_argument("command", choices=["group", "record", "reopen", "link-candidates", "summary"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", required=True)
    parser.add_argument("--items", help="group: JSON file with the gathered items")
    parser.add_argument("--records", help="record: JSON file with one record per project")
    parser.add_argument("--board", help="reopen: the board's data.json")
    args = parser.parse_args()
    try:
        if args.command == "group":
            if not args.items:
                parser.error("group needs --items")
            items = _load(Path(args.items))
            result: object = group(args.home, items if isinstance(items, list) else [], args.today)
        elif args.command == "record":
            if not args.records:
                parser.error("record needs --records")
            recs = _load(Path(args.records))
            if not isinstance(recs, list):
                parser.error("--records must be a JSON list")
            result = record(args.home, recs, args.today)
        elif args.command == "reopen":
            if not args.board:
                parser.error("reopen needs --board")
            result = reopen(args.home, args.board, args.today)
        elif args.command == "link-candidates":
            result = link_candidates(args.home, args.today)
        else:
            result = summary(args.home)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
