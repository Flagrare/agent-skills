"""When to talk to your manager, worked back from the packet deadline."""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta


def _dead(day: date, windows) -> bool:
    return any(start <= day <= end for start, end in windows)


def _back(start: date, days: int, windows) -> date:
    current = start
    remaining = days
    while remaining > 0:
        current -= timedelta(days=1)
        if not _dead(current, windows):
            remaining -= 1
    return current


def manager_conversation_window(
    packet_deadline: date,
    today: date,
    dead_windows=(),
    published: bool = False,
    peer_quote_days: int = 14,
    draft_days: int = 14,
    gap_days: int = 14,
    buffer_days: int = 14,
) -> dict:
    windows = list(dead_windows)
    absolute = _back(packet_deadline, peer_quote_days + draft_days + gap_days, windows)
    comfortable = _back(absolute, buffer_days, windows)
    if today > absolute:
        state = "past"
    elif today > comfortable:
        state = "tight"
    else:
        state = "ok"
    return {
        "absolute_by": absolute.isoformat(),
        "comfortable_by": comfortable.isoformat(),
        "status": "verified" if published else "inferred",
        "state": state,
        "assumptions": {
            "packet_deadline": packet_deadline.isoformat(),
            "dead_windows": [[s.isoformat(), e.isoformat()] for s, e in windows],
            "peer_quote_days": peer_quote_days,
            "draft_days": draft_days,
            "gap_days": gap_days,
            "buffer_days": buffer_days,
        },
    }


def _window(text: str) -> tuple[date, date]:
    start, end = text.split(":")
    return date.fromisoformat(start), date.fromisoformat(end)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manager-conversation window for a promotion cycle.")
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--dead", action="append", default=[], help="START:END, inclusive, repeatable")
    parser.add_argument("--published", action="store_true")
    args = parser.parse_args()
    result = manager_conversation_window(
        date.fromisoformat(args.deadline),
        date.fromisoformat(args.today),
        [_window(w) for w in args.dead],
        published=args.published,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
