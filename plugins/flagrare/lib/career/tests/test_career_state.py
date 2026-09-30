from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import career_state as cs  # noqa: E402

LEGACY = ".claude/skills/flagrare/senior-scan"
CAREER = ".claude/skills/flagrare/career"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


class ReadContributions(unittest.TestCase):
    def test_given_only_legacy_log_when_reading_then_returns_its_entries(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# Senior scan contributions\n\n- a\n- b\n")
            self.assertEqual(cs.read_contributions(str(home)), ["- a", "- b"])

    def test_given_both_logs_diverged_when_reading_then_returns_union_without_loss(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n- b\n- c\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n- d\n")
            self.assertEqual(cs.read_contributions(str(home)), ["- a", "- b", "- c", "- d"])

    def test_given_no_logs_when_reading_then_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cs.read_contributions(d), [])


class PlanMigration(unittest.TestCase):
    def test_given_brand_new_user_when_planning_then_only_creates_career_dir(self):
        with tempfile.TemporaryDirectory() as d:
            actions = cs.plan_migration(d)
            self.assertEqual([a["action"] for a in actions], ["mkdir"])

    def test_given_legacy_only_when_planning_then_copies_everything_and_adds_pointer(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n")
            write(home, f"{LEGACY}/state.json", '{"last_run": "2026-09-30"}')
            write(home, f"{LEGACY}/voice.md", "short sentences")
            actions = cs.plan_migration(str(home))
            written = {Path(a["path"]).name: a["content"] for a in actions if a["action"] == "write"}
            self.assertIn("- a", written["contributions.log.md"])
            self.assertEqual(written["scan-state.json"], '{"last_run": "2026-09-30"}')
            self.assertEqual(written["voice.md"], "short sentences")
            self.assertIn("career", written["MOVED.md"])

    def test_given_migration_already_applied_when_planning_again_then_plans_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n")
            for a in cs.plan_migration(str(home)):
                if a["action"] == "mkdir":
                    Path(a["path"]).mkdir(parents=True, exist_ok=True)
                else:
                    Path(a["path"]).write_text(a["content"])
            self.assertEqual(cs.plan_migration(str(home)), [])

    def test_given_career_log_has_extra_entries_when_planning_then_never_drops_them(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n- b\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n- z\n")
            log_writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            for entry in ("- a", "- b", "- z"):
                self.assertIn(entry, log_writes[0]["content"])

    def test_given_existing_career_state_when_planning_then_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", '{"old": true}')
            write(home, f"{CAREER}/scan-state.json", '{"new": true}')
            paths = [a["path"] for a in cs.plan_migration(str(home))]
            self.assertFalse(any(p.endswith("scan-state.json") for p in paths))


class Config(unittest.TestCase):
    def test_given_only_legacy_key_when_reading_impact_scan_config_then_falls_back(self):
        cfg = {"skills": {"senior-scan": {"domains": ["x"]}}}
        self.assertEqual(cs.skill_config(cfg, "impact-scan"), {"domains": ["x"]})

    def test_given_new_key_when_reading_impact_scan_config_then_prefers_it(self):
        cfg = {"skills": {"senior-scan": {"a": 1}, "impact-scan": {"b": 2}}}
        self.assertEqual(cs.skill_config(cfg, "impact-scan"), {"b": 2})

    def test_given_legacy_board_dir_when_resolving_then_falls_back(self):
        cfg = {"skills": {"senior-scan": {"board": {"dir": "~/b"}}}}
        self.assertEqual(cs.board_dir(cfg), "~/b")

    def test_given_no_board_when_resolving_then_none(self):
        self.assertIsNone(cs.board_dir({}))


class Cli(unittest.TestCase):
    def test_given_home_when_running_paths_then_prints_json_with_career_dir(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run(
                [sys.executable, str(Path(cs.__file__)), "paths", "--home", d],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertTrue(json.loads(out)["career_dir"].endswith("flagrare/career"))


if __name__ == "__main__":
    unittest.main()
