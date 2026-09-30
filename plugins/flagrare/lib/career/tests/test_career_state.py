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

    def test_given_legacy_entry_with_trailing_spaces_when_planning_again_then_does_not_reappend(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a  \n- b\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n")
            for a in cs.plan_migration(str(home)):
                if a["action"] == "mkdir":
                    Path(a["path"]).mkdir(parents=True, exist_ok=True)
                else:
                    Path(a["path"]).write_text(a["content"])
            again = cs.plan_migration(str(home))
            self.assertEqual([a for a in again if a["path"].endswith("contributions.log.md")], [])
            career_text = (home / CAREER / "contributions.log.md").read_text()
            self.assertEqual(career_text.splitlines().count("- a"), 1)

    def test_given_career_log_entry_with_trailing_spaces_when_planning_then_does_not_reappend(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a  \n- b\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a  \n")
            for a in cs.plan_migration(str(home)):
                Path(a["path"]).write_text(a["content"])
            again = cs.plan_migration(str(home))
            self.assertEqual([a for a in again if a["path"].endswith("contributions.log.md")], [])
            career_text = (home / CAREER / "contributions.log.md").read_text()
            self.assertEqual([l for l in career_text.splitlines() if l.rstrip() == "- a"], ["- a  "])

    def test_given_career_log_has_extra_entries_when_planning_then_never_drops_them(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n- b\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n- z\n")
            log_writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            for entry in ("- a", "- b", "- z"):
                self.assertIn(entry, log_writes[0]["content"])

    def test_given_existing_career_state_when_planning_then_keeps_career_values(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", '{"old": true}')
            write(home, f"{CAREER}/scan-state.json", '{"new": true}')
            writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("scan-state.json")]
            merged = json.loads(writes[0]["content"])
            self.assertTrue(merged["new"])
            self.assertTrue(merged["old"])

    def test_given_career_log_with_structure_when_planning_then_preserves_format(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            career_text = "# h\n\n- a\n  continuation line\n## notes\n\n- d\n"
            legacy_text = "# h\n\n- a\n- b\n"
            write(home, f"{LEGACY}/contributions.log.md", legacy_text)
            write(home, f"{CAREER}/contributions.log.md", career_text)
            actions = cs.plan_migration(str(home))
            log_writes = [a for a in actions if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            content = log_writes[0]["content"]
            self.assertIn("## notes", content)
            self.assertIn("  continuation line", content)
            self.assertIn("- b", content)
            lines = content.split('\n')
            notes_idx = next((i for i, l in enumerate(lines) if l == "## notes"), -1)
            cont_idx = next((i for i, l in enumerate(lines) if "continuation" in l), -1)
            b_idx = next((i for i, l in enumerate(lines) if l == "- b"), -1)
            self.assertGreater(notes_idx, -1)
            self.assertGreater(cont_idx, -1)
            self.assertGreater(b_idx, notes_idx)

    def test_given_legacy_with_paragraph_when_planning_then_copies_verbatim(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            legacy_text = "# h\n\nSome intro text.\n\n- a\n- b\n"
            write(home, f"{LEGACY}/contributions.log.md", legacy_text)
            actions = cs.plan_migration(str(home))
            log_writes = [a for a in actions if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            self.assertEqual(log_writes[0]["content"], legacy_text)


class ScanStateMerge(unittest.TestCase):
    def _plan_state(self, home: Path) -> dict:
        writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("scan-state.json")]
        return json.loads(writes[0]["content"]) if writes else {}

    def test_given_legacy_state_newer_when_planning_then_merge_takes_later_last_run_and_all_items(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05T10:00:00Z", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}, {"id": "b", "status": "surfaced", "surfaced_at": "2026-10-05"}]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30T10:00:00Z", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-09-30"}]}))
            merged = self._plan_state(home)
            self.assertEqual(merged["last_run"], "2026-10-05T10:00:00Z")
            self.assertEqual([i["id"] for i in merged["seen"]], ["a", "b"])

    def test_given_career_marks_item_contributed_when_merging_then_contributed_wins(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30", "seen": [{"id": "a", "status": "contributed", "surfaced_at": "2026-09-30"}]}))
            self.assertEqual(self._plan_state(home)["seen"][0]["status"], "contributed")

    def test_given_states_already_merged_when_planning_then_no_state_write(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            state = {"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}]}
            write(home, f"{LEGACY}/state.json", json.dumps(state))
            write(home, f"{CAREER}/scan-state.json", json.dumps(state))
            self.assertEqual(self._plan_state(home), {})

    def test_given_career_has_id_less_seen_items_when_merging_then_keeps_them(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30", "seen": [{"id": "b", "status": "surfaced", "surfaced_at": "2026-09-30"}, {"note": "noid"}]}))
            merged = self._plan_state(home)
            ids = [i.get("id") for i in merged["seen"]]
            self.assertEqual(ids[:2], ["a", "b"])
            self.assertTrue(any(i.get("note") == "noid" for i in merged["seen"]))

    def test_given_legacy_state_json_is_not_dict_when_planning_then_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps([1]))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30"}))
            self.assertEqual(self._plan_state(home), {})

    def test_given_seen_contains_non_dict_when_planning_then_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05", "seen": ["x"]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30"}))
            self.assertEqual(self._plan_state(home), {})

    def test_given_diverged_states_when_planning_and_applying_then_replan_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            legacy_state = {"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}, {"note": "legacy_noid"}]}
            career_state = {"last_run": "2026-09-30", "seen": [{"id": "b", "status": "surfaced", "surfaced_at": "2026-09-30"}, {"note": "career_noid"}]}
            write(home, f"{LEGACY}/state.json", json.dumps(legacy_state))
            write(home, f"{CAREER}/scan-state.json", json.dumps(career_state))
            actions = cs.plan_migration(str(home))
            state_writes = [a for a in actions if a["path"].endswith("scan-state.json")]
            self.assertTrue(len(state_writes) > 0)
            Path(state_writes[0]["path"]).write_text(state_writes[0]["content"])
            again = cs.plan_migration(str(home))
            replan_state_writes = [a for a in again if a["path"].endswith("scan-state.json")]
            self.assertEqual(len(replan_state_writes), 0)


class VoiceCopy(unittest.TestCase):
    def test_given_legacy_voice_newer_and_different_when_planning_then_copies_it(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/voice.md", "old rules")
            write(home, f"{LEGACY}/voice.md", "new rules")
            os.utime(home / CAREER / "voice.md", (1_000_000, 1_000_000))
            writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("voice.md")]
            self.assertEqual(writes[0]["content"], "new rules")

    def test_given_career_voice_newer_when_planning_then_keeps_it(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/voice.md", "legacy rules")
            write(home, f"{CAREER}/voice.md", "edited rules")
            os.utime(home / LEGACY / "voice.md", (1_000_000, 1_000_000))
            self.assertFalse([a for a in cs.plan_migration(str(home)) if a["path"].endswith("voice.md")])


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
