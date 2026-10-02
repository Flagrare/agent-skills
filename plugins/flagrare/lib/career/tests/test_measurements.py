from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measurements as m  # noqa: E402

CAREER = ".claude/skills/flagrare/career"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def entry(**over) -> dict:
    base = {
        "id": "acme-reorder",
        "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
        "stage": "before",
        "metric": {"name": "repeat orders per week", "why": "the button exists to bring people back"},
        "source": {"category": "data warehouse", "tool": "warehouse", "query": "select count(*) from orders", "run_at": "2026-10-01"},
        "baseline": {"value": "120 a week", "as_of": "2026-10-01", "confidence": "direct"},
        "bet": {"sentence": "We believe a reorder button will lift repeat orders, because Kai's survey says people retype orders", "range": "130 to 160 a week", "confidence": "inferred"},
        "ownership": "mine",
    }
    base.update(over)
    return base


class Load(unittest.TestCase):
    def test_given_no_file_when_loading_then_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.load(d), [])

    def test_given_a_valid_file_when_loading_then_returns_its_entries(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([entry()]))
            self.assertEqual(m.load(d)[0]["id"], "acme-reorder")

    def test_given_a_corrupt_file_when_loading_then_refuses_instead_of_returning_empty(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{not json")
            with self.assertRaises(m.CorruptFile):
                m.load(d)

    def test_given_a_file_that_is_not_a_list_when_loading_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "{}")
            with self.assertRaises(m.CorruptFile):
                m.load(d)


class CheckEntry(unittest.TestCase):
    def test_given_a_complete_entry_when_checking_then_accepts_it(self):
        m.check_entry(entry())

    def test_given_an_unknown_stage_when_checking_then_names_the_allowed_stages(self):
        with self.assertRaisesRegex(ValueError, "stage must be one of"):
            m.check_entry(entry(stage="during"))

    def test_given_an_unknown_confidence_level_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "2026-10-01", "confidence": "pretty sure"})
        with self.assertRaisesRegex(ValueError, "baseline confidence must be one of"):
            m.check_entry(bad)

    def test_given_an_unknown_ownership_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "ownership must be one of"):
            m.check_entry(entry(ownership="everyone"))

    def test_given_work_without_a_title_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "work needs a title"):
            m.check_entry(entry(work={"title": "", "link": "x", "kind": "ticket"}))

    def test_given_a_badly_formatted_date_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "Oct 1", "confidence": "direct"})
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            m.check_entry(bad)


def applied(actions: list[dict]) -> list[dict]:
    assert len(actions) == 1 and actions[0]["action"] == "write"
    return json.loads(actions[0]["content"])


class PlanUpsert(unittest.TestCase):
    def test_given_no_file_when_planning_then_writes_the_entry_with_its_query_verbatim(self):
        with tempfile.TemporaryDirectory() as d:
            q = "select count(*)\n  from orders where venue = 'acme'  -- kept as typed"
            items = applied(m.plan_upsert(d, entry(source={"category": "data warehouse", "tool": "warehouse", "query": q, "run_at": "2026-10-01"}), "2026-10-02"))
            self.assertEqual(items[0]["source"]["query"], q)
            self.assertEqual((items[0]["created_at"], items[0]["updated_at"]), ("2026-10-02", "2026-10-02"))

    def test_given_the_same_id_when_planning_again_then_updates_instead_of_duplicating(self):
        with tempfile.TemporaryDirectory() as d:
            first = applied(m.plan_upsert(d, entry(), "2026-10-01"))
            first[0]["checks"] = [{"due": "2026-10-15", "done_at": "2026-10-15", "value": "150", "verdict": "worked"}]
            first[0]["launch_date"] = "2026-10-01"
            write(Path(d), f"{CAREER}/measurements.json", json.dumps(first))
            items = applied(m.plan_upsert(d, entry(bet={"sentence": "We believe more", "range": "140 to 170", "confidence": "inferred"}), "2026-10-03"))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["bet"]["range"], "140 to 170")
            self.assertEqual(items[0]["checks"][0]["verdict"], "worked")
            self.assertEqual((items[0]["created_at"], items[0]["updated_at"]), ("2026-10-01", "2026-10-03"))

    def test_given_a_checked_measurement_when_planning_it_again_as_before_then_it_stays_after(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([{**entry(), "stage": "after", "created_at": "2026-10-01"}]))
            items = applied(m.plan_upsert(d, entry(), "2026-10-20"))
            self.assertEqual(items[0]["stage"], "after")

    def test_given_a_query_with_a_credential_when_planning_then_refuses_without_echoing_it(self):
        with tempfile.TemporaryDirectory() as d:
            bad = entry(source={"category": "api", "tool": "http", "query": "curl -H 'Authorization: Bearer abc123secret' https://api.example", "run_at": "2026-10-01"})
            with self.assertRaises(ValueError) as ctx:
                m.plan_upsert(d, bad, "2026-10-02")
            self.assertNotIn("abc123secret", str(ctx.exception))

    def test_given_a_password_in_a_query_when_planning_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            bad = entry(source={"category": "db", "tool": "psql", "query": "psql postgres://u:pw@h/db password=hunter2", "run_at": "2026-10-01"})
            with self.assertRaisesRegex(ValueError, "credential"):
                m.plan_upsert(d, bad, "2026-10-02")

    def test_given_a_corrupt_file_when_planning_then_refuses_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{oops")
            with self.assertRaises(m.CorruptFile):
                m.plan_upsert(d, entry(), "2026-10-02")

def saved(home: str, items: list[dict]) -> None:
    write(Path(home), f"{CAREER}/measurements.json", json.dumps(items))


class PlanLaunch(unittest.TestCase):
    def test_given_a_launch_date_when_launching_then_checks_fall_two_and_six_weeks_later(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry()])
            items = applied(m.plan_launch(d, "acme-reorder", "2026-10-01", "2026-10-02"))
            self.assertEqual(items[0]["launch_date"], "2026-10-01")
            self.assertEqual([c["due"] for c in items[0]["checks"]], ["2026-10-15", "2026-11-12"])

    def test_given_a_done_check_when_relaunching_then_keeps_it_and_moves_only_undone_ones(self):
        with tempfile.TemporaryDirectory() as d:
            done = {"due": "2026-10-15", "done_at": "2026-10-15", "value": "150", "verdict": "worked"}
            saved(d, [entry(launch_date="2026-10-01", checks=[done, {"due": "2026-11-12", "done_at": None, "value": None, "verdict": None}])])
            items = applied(m.plan_launch(d, "acme-reorder", "2026-10-08", "2026-10-16"))
            self.assertEqual(items[0]["checks"][0], done)
            self.assertEqual(items[0]["checks"][1]["due"], "2026-11-19")

    def test_given_an_unknown_id_when_launching_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "no measurement with id"):
                m.plan_launch(d, "nope", "2026-10-01", "2026-10-02")


class PlanCheck(unittest.TestCase):
    def test_given_a_due_check_when_recording_it_then_marks_it_done_and_the_entry_after(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(launch_date="2026-10-01", checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            items = applied(m.plan_check(d, "acme-reorder", "2026-10-15", "150 a week", "worked", "2026-10-16"))
            self.assertEqual(items[0]["checks"][0], {"due": "2026-10-15", "done_at": "2026-10-16", "value": "150 a week", "verdict": "worked"})
            self.assertEqual(items[0]["stage"], "after")

    def test_given_an_unknown_verdict_when_recording_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            with self.assertRaisesRegex(ValueError, "verdict must be one of"):
                m.plan_check(d, "acme-reorder", "2026-10-15", "150", "great", "2026-10-16")

    def test_given_no_check_on_that_date_when_recording_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            with self.assertRaisesRegex(ValueError, "no check due on 2026-10-20"):
                m.plan_check(d, "acme-reorder", "2026-10-20", "150", "worked", "2026-10-21")


class PlanSkip(unittest.TestCase):
    def test_given_a_small_fix_when_skipping_then_records_it_with_the_reason(self):
        with tempfile.TemporaryDirectory() as d:
            items = applied(m.plan_skip(d, "typo-fix", "Fix a typo on the menu page", "https://tracker.example/T-9", "ticket", "small fix, nothing users notice", "2026-10-02"))
            self.assertEqual((items[0]["stage"], items[0]["skipped_reason"]), ("skipped", "small fix, nothing users notice"))

    def test_given_an_existing_measurement_when_skipping_then_keeps_its_history(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry()])
            items = applied(m.plan_skip(d, "acme-reorder", "Reorder button for Acme Pizza", "https://tracker.example/T-1", "ticket", "dropped from the sprint", "2026-10-02"))
            self.assertEqual(len(items), 1)
            self.assertEqual((items[0]["stage"], items[0]["bet"]["range"]), ("skipped", "130 to 160 a week"))

LOG = ".claude/skills/flagrare/career/contributions.log.md"


class Due(unittest.TestCase):
    def test_given_nothing_saved_when_asking_then_nothing_is_due(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.due(d, "2026-10-02")["count"], 0)

    def test_given_a_check_past_its_date_when_asking_then_lists_it_and_not_a_future_one(self):
        with tempfile.TemporaryDirectory() as d:
            checks = [{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None},
                      {"due": "2026-11-12", "done_at": None, "value": None, "verdict": None}]
            saved(d, [entry(launch_date="2026-10-01", checks=checks)])
            result = m.due(d, "2026-10-16")
            self.assertEqual(result["checks_due"], [{"id": "acme-reorder", "title": "Reorder button for Acme Pizza", "due": "2026-10-15"}])

    def test_given_a_bet_with_no_launch_after_30_days_when_asking_then_lists_it_as_waiting(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [{**entry(), "created_at": "2026-09-01"}, {**entry(id="fresh"), "created_at": "2026-09-25"}])
            self.assertEqual([b["id"] for b in m.due(d, "2026-10-02")["bets_waiting"]], ["acme-reorder"])

    def test_given_log_entries_when_asking_then_lists_only_those_with_no_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), LOG, "# log\n\n"
                  "- 2026-09-20 | https://tracker.example/T-1 | Shipped the reorder button | behavior: x\n"
                  "- 2026-09-21 | https://chat.example/p1 | Answered Sam on payouts | behavior: y\n"
                  "- 2026-09-22 | https://docs.example/d2). | Wrote the onboarding doc | behavior: z\n")
            saved(d, [entry(), {"id": "d2", "work": {"title": "doc", "link": "https://docs.example/d2", "kind": "log_entry"}, "stage": "skipped", "skipped_reason": "no number possible"}])
            wins = m.due(d, "2026-10-02")["unmeasured_wins"]
            self.assertEqual([w["link"] for w in wins], ["https://chat.example/p1"])

    def test_given_an_old_log_when_asking_then_only_the_last_30_days_count_unless_asked_for_all(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), LOG, "- 2026-08-01 | https://chat.example/old | An old win | behavior: x\n"
                  "- 2026-09-25 | https://chat.example/new | A recent win | behavior: x\n")
            self.assertEqual([w["link"] for w in m.due(d, "2026-10-02")["unmeasured_wins"]], ["https://chat.example/new"])
            self.assertEqual(len(m.due(d, "2026-10-02", wins_since="")["unmeasured_wins"]), 2)

    def test_given_odd_log_lines_when_asking_then_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), LOG, "- 2026-09-20 | Shipped without a link\n-   \n- not | enough\n")
            result = m.due(d, "2026-10-02")
            self.assertIsInstance(result["unmeasured_wins"], list)

    def test_given_a_query_with_quotes_in_an_entry_file_when_planning_from_the_command_line_then_keeps_it_verbatim(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            q = "select count(*) from orders where venue = 'acme' and note = \"it's\""
            f = Path(d) / "entry.json"
            f.write_text(json.dumps(entry(source={"category": "data warehouse", "tool": "warehouse", "query": q, "run_at": "2026-10-01"})))
            script = Path(__file__).resolve().parents[1] / "measurements.py"
            out = subprocess.run([sys.executable, str(script), "plan", "--home", d, "--today", "2026-10-02", "--entry-file", str(f)],
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(json.loads(json.loads(out)[0]["content"])[0]["source"]["query"], q)

    def test_given_a_skipped_entry_with_an_overdue_check_when_asking_then_stays_silent(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(stage="skipped", skipped_reason="dropped", checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            self.assertEqual(m.due(d, "2026-10-20")["checks_due"], [])

class ReviewFixes(unittest.TestCase):
    def test_given_an_entry_sent_with_empty_checks_and_launch_when_planning_again_then_keeps_the_saved_ones(self):
        with tempfile.TemporaryDirectory() as d:
            done = {"due": "2026-10-15", "done_at": "2026-10-15", "value": "150", "verdict": "worked", "after_days": 14}
            saved(d, [{**entry(), "stage": "after", "launch_date": "2026-10-01", "checks": [done], "created_at": "2026-09-20"}])
            items = applied(m.plan_upsert(d, {**entry(stage="after"), "launch_date": None, "checks": [], "created_at": "2026-10-20"}, "2026-10-20"))
            self.assertEqual((items[0]["launch_date"], items[0]["checks"], items[0]["created_at"]), ("2026-10-01", [done], "2026-09-20"))

    def test_given_common_credential_shapes_in_a_query_when_planning_then_refuses_each(self):
        shapes = ['curl -d \'{"password": "hunter2"}\' https://api.example',
                  '{"token": "abc123"}',
                  'curl -u kai:hunter2 https://api.example',
                  'snowsql -a acct --password hunter2',
                  'curl -H "x: ghp_abcdefghijklmnop1234" https://api.example',
                  'aws s3 ls --key AKIAABCDEFGHIJKLMNOP']
        for q in shapes:
            with self.subTest(q=q), tempfile.TemporaryDirectory() as d:
                with self.assertRaisesRegex(ValueError, "credential"):
                    m.plan_upsert(d, entry(source={"category": "api", "tool": "http", "query": q, "run_at": "2026-10-01"}), "2026-10-02")

    def test_given_a_port_flag_in_a_query_when_planning_then_does_not_mistake_it_for_a_password(self):
        with tempfile.TemporaryDirectory() as d:
            q = "psql -h db.example -p 5432 -c 'select 1'"
            items = applied(m.plan_upsert(d, entry(source={"category": "db", "tool": "psql", "query": q, "run_at": "2026-10-01"}), "2026-10-02"))
            self.assertEqual(items[0]["source"]["query"], q)

    def test_given_only_the_six_week_check_done_when_relaunching_then_keeps_it_and_moves_the_two_week_one(self):
        with tempfile.TemporaryDirectory() as d:
            six = {"due": "2026-11-12", "done_at": "2026-11-12", "value": "160", "verdict": "worked", "after_days": 42}
            two = {"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14}
            saved(d, [entry(launch_date="2026-10-01", checks=[two, six])])
            items = applied(m.plan_launch(d, "acme-reorder", "2026-10-08", "2026-11-13"))
            self.assertEqual(sorted((c["after_days"], c["due"], bool(c["done_at"])) for c in items[0]["checks"]),
                             [(14, "2026-10-22", False), (42, "2026-11-12", True)])


if __name__ == "__main__":
    unittest.main()
