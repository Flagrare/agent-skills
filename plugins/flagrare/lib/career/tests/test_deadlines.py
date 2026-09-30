from __future__ import annotations
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deadlines as dl  # noqa: E402

HOLIDAYS = [(date(2026, 12, 20), date(2027, 1, 2))]


class Window(unittest.TestCase):
    def test_given_last_years_calendar_and_holidays_when_computing_then_late_oct_and_mid_nov(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS)
        self.assertEqual(w["absolute_by"], "2026-11-12")
        self.assertEqual(w["comfortable_by"], "2026-10-29")
        self.assertEqual(w["state"], "ok")

    def test_given_unpublished_calendar_when_computing_then_marked_inferred(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS)
        self.assertEqual(w["status"], "inferred")

    def test_given_published_calendar_when_computing_then_marked_verified(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS, published=True)
        self.assertEqual(w["status"], "verified")

    def test_given_today_between_comfortable_and_absolute_when_computing_then_tight(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 11, 5), HOLIDAYS)
        self.assertEqual(w["state"], "tight")

    def test_given_today_after_absolute_when_computing_then_past(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 12, 1), HOLIDAYS)
        self.assertEqual(w["state"], "past")

    def test_given_deadline_inside_holidays_when_computing_then_skips_dead_days(self):
        w = dl.manager_conversation_window(date(2026, 12, 25), date(2026, 9, 1), HOLIDAYS)
        self.assertEqual(w["absolute_by"], "2026-11-08")

    def test_given_no_dead_windows_when_computing_then_counts_plain_days(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30))
        self.assertEqual(w["absolute_by"], "2026-11-26")
        self.assertEqual(w["comfortable_by"], "2026-11-12")


if __name__ == "__main__":
    unittest.main()
