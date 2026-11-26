"""Where the user stands on each next-level behavior, against the company's promotion bar. Read-only.

The promotion skill rates each rubric row (`assessment`: meets or not yet at the
target level, exceeds, meets or below at the current level, since when, why and
with what proof). This module only reads those ratings, the bar the map quotes
from the company's own process (`process.bar`: about how many months a behavior
must already be met before the promotion takes effect) and the effective date,
and says which rows hold for the bar and which rows are due for a new rating.
"""
from __future__ import annotations

from datetime import date

TARGET_RATINGS = {"meets", "not_yet"}
CURRENT_RATINGS = {"exceeds", "meets", "below"}
RERATE_DAYS = 14


def _value(fact: object) -> object:
    return fact.get("value") if isinstance(fact, dict) else fact


def _date(text: object) -> date | None:
    try:
        return date.fromisoformat(text) if isinstance(text, str) else None
    except ValueError:
        return None


def _months_before(d: date, months: int) -> date:
    """The same day `months` earlier, clamped to the month's last day."""
    total = d.year * 12 + d.month - 1 - months
    year, month = divmod(total, 12)
    month += 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    return date(year, month, 28)


def _whole_months(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month) - (1 if end.day < start.day else 0)
    return max(months, 0)


def rows(m: dict) -> list[dict]:
    return [r for r in ((m.get("rubric") or {}).get("rows") or []) if isinstance(r, dict) and r.get("id")]


def rating(row: dict) -> dict | None:
    """The row's assessment, or None when it has not been rated yet."""
    rated_as = row.get("assessment")
    return rated_as if isinstance(rated_as, dict) and rated_as.get("target") in TARGET_RATINGS else None


def bar(m: dict) -> dict:
    """The company's bar: months met before the effective date, and the date a behavior must be met by."""
    bar_value = _value((m.get("process") or {}).get("bar"))
    months = bar_value.get("months") if isinstance(bar_value, dict) else None
    months = months if isinstance(months, int) and not isinstance(months, bool) and months >= 0 else None
    effective = _date(_value((m.get("calendar") or {}).get("effective")))
    met_by = _months_before(effective, months) if effective and months is not None else None
    return {"months": months, "effective": effective.isoformat() if effective else None,
            "met_by": met_by.isoformat() if met_by else None,
            "text": bar_value.get("text", "") if isinstance(bar_value, dict) else ""}


def _classify(row: dict, met_by: date | None, now: date) -> dict:
    """One row's standing: its rating (or its status when not rated yet), since when it has met the next level,
    and whether that is long enough for the bar."""
    rated_as = rating(row) or {}
    if rated_as:
        is_met = rated_as["target"] == "meets"
        since = _date(rated_as.get("since")) if is_met else None
    else:
        is_met = row.get("status") == "done"
        since = None
    current = rated_as.get("current") if rated_as.get("current") in CURRENT_RATINGS else None
    return {"id": row["id"], "label": row.get("label") or row["id"], "area": row.get("area", ""), "rated": bool(rated_as),
            "target": "meets" if is_met else "not_yet", "current": current,
            "since": since.isoformat() if since else None,
            "months_held": _whole_months(since, now) if since else None,
            "holds": (since <= met_by) if since and met_by else None,
            "reason": rated_as.get("reason", ""), "proof": list(rated_as.get("proof") or []),
            "checked_at": rated_as.get("checked_at"), "next_step": row.get("next_step", "")}


def summary(m: dict, today: str) -> dict:
    """X of N next-level behaviors met, which hold for the bar, which are not yet, and where the user exceeds today.
    Rows with no rating fall back to their status (done counts as met), so older maps still show a count."""
    now = date.fromisoformat(today)
    bar_info = bar(m)
    standing = [_classify(row, _date(bar_info["met_by"]), now) for row in rows(m)]
    met = [r for r in standing if r["target"] == "meets"]
    return {"total": len(standing), "met": len(met), "rated": sum(r["rated"] for r in standing),
            "unrated": sum(not r["rated"] for r in standing),
            "holding": sum(r["holds"] is True for r in met), "short": sum(r["holds"] is False for r in met),
            "bar": bar_info,
            "not_yet": [{"id": r["id"], "label": r["label"], "reason": r["reason"], "next_step": r["next_step"]}
                        for r in standing if r["target"] != "meets"],
            "exceeding": [{"id": r["id"], "label": r["label"]} for r in standing if r["current"] == "exceeds"],
            "rows": standing}


def due_rows(m: dict, log: list[tuple[str, str | None]], today: str, days: int = RERATE_DAYS) -> list[dict]:
    """Rows to rate again, in map order, each with a plain why: never rated, new proof tagged with the row
    since its last rating, or not rated in `days` days."""
    now = date.fromisoformat(today)
    out = []
    for row in rows(m):
        rated_as = rating(row)
        label = row.get("label") or row["id"]
        checked = _date((rated_as or {}).get("checked_at"))
        if not rated_as or not checked:
            out.append({"id": row["id"], "label": label, "why": "not rated yet"})
            continue
        newer = [d for d, rid in log if rid == row["id"] and (_date(d) or checked) > checked]
        if newer:
            out.append({"id": row["id"], "label": label, "why": "new proof"})
        elif (now - checked).days > days:
            out.append({"id": row["id"], "label": label, "why": f"not rated in {days} days"})
    return out


def describe(due: list[dict]) -> str:
    """One plain sentence for the coordinator's why, grouped by reason, behaviors by label."""
    groups: dict[str, list[str]] = {}
    for d in due:
        groups.setdefault(d["why"], []).append(d["label"])
    return "; ".join(f"{why}: {', '.join(labels)}" for why, labels in groups.items())


def validate(m: dict) -> list[str]:
    """Errors in the rows' ratings. A row without an assessment is fine (not rated yet)."""
    errors = []
    for i, row in enumerate(((m.get("rubric") or {}).get("rows") or [])):
        if not isinstance(row, dict) or "assessment" not in row:
            continue
        rated_as, path = row["assessment"], f"rubric.rows[{i}].assessment"
        if not isinstance(rated_as, dict):
            errors.append(f"{path}: must be an object")
            continue
        if rated_as.get("target") not in TARGET_RATINGS:
            errors.append(f"{path}: target must be one of {sorted(TARGET_RATINGS)}")
        if "current" in rated_as and rated_as["current"] not in CURRENT_RATINGS:
            errors.append(f"{path}: current must be one of {sorted(CURRENT_RATINGS)}")
        checked = _date(rated_as.get("checked_at"))
        if checked is None:
            errors.append(f"{path}: checked_at must be an ISO date (YYYY-MM-DD)")
        since = _date(rated_as.get("since"))
        if "since" in rated_as and since is None:
            errors.append(f"{path}: since must be an ISO date (YYYY-MM-DD)")
        elif rated_as.get("target") == "meets" and since is None:
            errors.append(f"{path}: since (the date it first met the next level) is required when target is meets")
        if since and checked and since > checked:
            errors.append(f"{path}: since is after checked_at")
    return errors
