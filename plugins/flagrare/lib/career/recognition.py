"""Recognition from a peer-recognition platform (Bonusly first), as proof for the career skills.

Reads only. `fetch` calls the platform with the user's personal token and prints a planned write of
`career/recognition.json` (the skill writes it with the Write tool); every other command reads that
cache, so the board and digests never need the network. The token lives outside the repo and the
config, in a file the user owns (default `~/.config/flagrare/bonusly-token`).
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import career_state

API = "https://bonus.ly/api/v1"
DEFAULT_TOKEN_FILE = "~/.config/flagrare/bonusly-token"
PAGE = 100
MAX_PAGES = 20


def settings(home: str) -> dict:
    """The recognition block of the shared config (`skills.career.recognition`), with defaults."""
    try:
        config = json.loads(Path(career_state.paths(home)["config"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}
    block = ((config.get("skills") or {}).get("career") or {}).get("recognition") or {}
    return {"provider": block.get("provider", "bonusly"),
            "token_file": block.get("token_file", DEFAULT_TOKEN_FILE),
            "enabled": block.get("enabled", True)}


def read_token(home: str) -> str | None:
    raw = settings(home)["token_file"]
    path = Path(home) / raw[2:] if raw.startswith("~/") else Path(raw)
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """The API never redirects; refusing keeps the token from being forwarded to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(f"recognition platform redirected to {urllib.parse.urlparse(newurl).netloc}; not following it with the token")


def _default_opener(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.build_opener(_NoRedirect).open(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _get(path: str, params: dict, token: str, opener: Callable[[str, str], dict]) -> object:
    url = f"{API}{path}?{urllib.parse.urlencode(params)}" if params else f"{API}{path}"
    body = opener(url, token)
    if not isinstance(body, dict) or not body.get("success"):
        raise RuntimeError(f"recognition platform refused {path}: {body.get('message') if isinstance(body, dict) else body}")
    return body.get("result")


def clean_text(reason: str) -> str:
    """The thanks in plain words: no images, point amounts, hashtags or leading @-handles."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", reason or "")
    text = re.sub(r"(?<!\w)[+]\d+\b", " ", text)
    text = re.sub(r"(?<!\w)#[\w-]+", " ", text)
    text = re.sub(r"^(\s*,?\s*(and\s+)?@[\w.-]+\s*,?)+", " ", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip(" ,")


def normalize(bonus: dict) -> dict:
    """One bonus as proof: who gave it, for what, tagged with which company value, and the +1s others added."""
    giver = bonus.get("giver") or {}
    children = bonus.get("child_bonuses")
    plus_ones = [(c.get("giver") or {}).get("full_name", "") for c in children] if isinstance(children, list) else []
    return {
        "id": bonus.get("id"),
        "date": str(bonus.get("created_at", ""))[:10],
        "giver": {"name": giver.get("full_name", ""), "email": giver.get("email", "")},
        "receivers": [r.get("full_name", "") for r in (bonus.get("receivers") or []) if isinstance(r, dict)],
        "value": bonus.get("value") or str(bonus.get("hashtag") or "").lstrip("#"),
        "reason": bonus.get("reason_decoded") or bonus.get("reason", ""),
        "text": clean_text(bonus.get("reason_decoded") or bonus.get("reason", "")),
        "plus_ones": [p for p in plus_ones if p] or [],
        "plus_one_count": len(plus_ones) if plus_ones else int(bonus.get("child_count") or 0),
        "link": f"https://bonus.ly/bonuses/{bonus.get('id')}",
    }


def fetch(token: str, since: str, until: str, opener: Callable[[str, str], dict] = _default_opener) -> dict:
    """The user's received and given recognition between two dates, newest first."""
    me = _get("/users/me", {}, token, opener) or {}
    email = me.get("email", "")
    if not email:
        raise RuntimeError("the recognition platform did not return your email, so the bonuses can't be filtered to you")
    start = f"{since}T00:00:00Z"
    end = f"{(date.fromisoformat(until) + timedelta(days=1)).isoformat()}T00:00:00Z"
    out = {}
    for key, who in (("received", "receiver_email"), ("given", "giver_email")):
        items, skip = [], 0
        for _ in range(MAX_PAGES):
            page = _get("/bonuses", {who: email, "start_time": start, "end_time": end, "limit": PAGE,
                                     "skip": skip, "include_children": "true"}, token, opener) or []
            items += [normalize(b) for b in page if isinstance(b, dict)]
            if len(page) < PAGE:
                break
            skip += PAGE
        out[key] = items
    return {"user": {"name": me.get("full_name", ""), "email": email, "manager_email": me.get("manager_email", "")},
            "since": since, "until": until, **out}


def plan_fetch(home: str, today: str, since: str | None = None, opener: Callable[[str, str], dict] = _default_opener) -> list[dict]:
    """Plan career/recognition.json with everything since `since` (default: one year back)."""
    if not settings(home)["enabled"]:
        raise ValueError("recognition is turned off (skills.career.recognition.enabled is false)")
    token = read_token(home)
    if token is None:
        raise ValueError(f"no recognition token: put a personal token in {settings(home)['token_file']}")
    since = since or (date.fromisoformat(today) - timedelta(days=365)).isoformat()
    data = {"fetched_on": today, "provider": settings(home)["provider"], **fetch(token, since, today, opener)}
    path = str(Path(career_state.paths(home)["career_dir"]) / "recognition.json")
    return [{"action": "write", "path": path, "content": json.dumps(data, indent=2, ensure_ascii=False) + "\n",
             "reason": f"cache {len(data['received'])} received and {len(data['given'])} given recognitions"}]


def load(home: str) -> dict | None:
    try:
        data = json.loads((Path(career_state.paths(home)["career_dir"]) / "recognition.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def summary(home: str, today: str) -> dict:
    """What the cache says: totals, the last 30 days, company values, and who recognized the user most (first-hand witnesses)."""
    data = load(home)
    if data is None:
        return {"has_recognition": False}
    received = [b for b in data.get("received") or [] if isinstance(b, dict)]
    given = [b for b in data.get("given") or [] if isinstance(b, dict)]
    start = (date.fromisoformat(today) - timedelta(days=29)).isoformat()
    givers: dict[str, dict] = {}
    for b in received:
        g = b.get("giver") or {}
        key = g.get("email") or g.get("name")
        if not key:
            continue
        entry = givers.setdefault(key, {"name": g.get("name", ""), "email": g.get("email", ""), "count": 0, "last": "", "values": Counter()})
        entry["count"] += 1
        entry["last"] = max(entry["last"], b.get("date", ""))
        if b.get("value"):
            entry["values"][b["value"]] += 1
    ranked = sorted(givers.values(), key=lambda e: (-e["count"], e["name"]))
    return {
        "has_recognition": True,
        "fetched_on": data.get("fetched_on"),
        "received": len(received),
        "received_last_30_days": sum(1 for b in received if start <= b.get("date", "") <= today),
        "given": len(given),
        "values": Counter(b["value"] for b in received if b.get("value")).most_common(),
        "givers": [{**g, "values": [v for v, _ in g["values"].most_common(3)]} for g in ranked],
        "latest": sorted(received, key=lambda b: b.get("date", ""), reverse=True)[:3],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only recognition source for the career skills.")
    parser.add_argument("command", choices=["fetch", "summary"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", required=True)
    parser.add_argument("--since", help="fetch: first day to read (default: one year back)")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.today)
        result = plan_fetch(args.home, args.today, args.since) if args.command == "fetch" else summary(args.home, args.today)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
