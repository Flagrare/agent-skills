"""Measurements of the impact of the user's work, for /flagrare:measure-impact.

Plan-only, like career_state.py: nothing here writes a file. Commands print planned writes
of career/measurements.json as JSON, and the skill applies them with the Write tool.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path

import career_state

STAGES = ["before", "after", "past", "skipped"]
CONFIDENCE = ["direct", "supported", "inferred", "speculative", "unknown"]
OWNERSHIP = ["mine", "team", "contributed"]
KINDS = ["ticket", "tdd", "project", "log_entry"]
VERDICTS = ["worked", "didnt_work", "cant_tell"]
CHECK_DAYS = (14, 42)
BET_WAIT_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CorruptFile(ValueError):
    """measurements.json exists but can't be read; never plan over it."""


def file_path(home: str) -> Path:
    return Path(career_state.paths(home)["measurements"])


def load(home: str) -> list[dict]:
    path = file_path(home)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorruptFile(f"{path} is not valid JSON ({exc.msg}); fix or move it before measuring again") from exc
    if not isinstance(data, list):
        raise CorruptFile(f"{path} must hold a list of measurements")
    return data


def _check_date(name: str, value: object) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValueError(f"{name} must be a date written YYYY-MM-DD")
    date.fromisoformat(value)


def _check_confidence(name: str, block: object) -> None:
    if not isinstance(block, dict) or "confidence" not in block:
        return
    if block["confidence"] not in CONFIDENCE:
        raise ValueError(f"{name} confidence must be one of {CONFIDENCE}")


def check_entry(entry: dict) -> None:
    if not isinstance(entry, dict) or not entry.get("id"):
        raise ValueError("a measurement needs an id")
    work = entry.get("work") or {}
    if not work.get("title"):
        raise ValueError("work needs a title")
    if work.get("kind") not in KINDS:
        raise ValueError(f"work kind must be one of {KINDS}")
    if entry.get("stage") not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    if "ownership" in entry and entry["ownership"] not in OWNERSHIP:
        raise ValueError(f"ownership must be one of {OWNERSHIP}")
    for name in ("baseline", "comparable", "bet", "result"):
        _check_confidence(name, entry.get(name))
    _check_date("baseline as_of", (entry.get("baseline") or {}).get("as_of"))
    _check_date("source run_at", (entry.get("source") or {}).get("run_at"))
    _check_date("launch_date", entry.get("launch_date"))
