from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measure_reminders as mr  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
CONFIG = ".claude/skills/flagrare/config.json"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def measurement(**over) -> dict:
    base = {"id": "acme-reorder", "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
            "stage": "before", "launch_date": "2026-10-01",
            "checks": [{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14}],
            "created_at": "2026-09-20", "updated_at": "2026-10-01"}
    base.update(over)
    return base


class SessionStart(unittest.TestCase):
    def test_given_nothing_saved_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_check_due_when_a_session_starts_then_shows_one_line_and_tells_claude_the_details(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 1 check due (Reorder button for Acme Pizza). Ask Claude to measure it when you have a minute.")
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertIn("acme-reorder", out["hookSpecificOutput"]["additionalContext"])

    def test_given_checks_and_recent_wins_due_when_a_session_starts_then_counts_each_kind(self):
        with tempfile.TemporaryDirectory() as d:
            two = measurement(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14},
                                      {"due": "2026-10-16", "done_at": None, "value": None, "verdict": None, "after_days": 42}])
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([two]))
            write(Path(d), f"{CAREER}/contributions.log.md", "- 2026-10-10 | https://chat.example/p1 | Helped Sam | behavior: x\n")
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 2 checks due (Reorder button for Acme Pizza, and more), 1 recent win with no number. Ask Claude to measure them when you have a minute.")

    def test_given_reminders_turned_off_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": False}}}))
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_corrupt_file_when_a_session_starts_then_names_the_file_in_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{oops")
            out = mr.session_start(d, "2026-10-16")
            self.assertIn("measurements.json", out["systemMessage"])
            self.assertNotIn("Traceback", out["systemMessage"])


def skill_event(name: str, args: str = "", sid: str = "s1") -> dict:
    return {"session_id": sid, "hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": {"skill": name, "args": args}}


class Moment(unittest.TestCase):
    def test_given_a_tdd_was_drafted_when_the_tool_finishes_then_tells_claude_to_offer_a_before_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            out = mr.moment(skill_event("flagrare:tdd-writer", "T-5"), d, s)
            note = out["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
            self.assertIn("a TDD is being written", note)
            self.assertIn("before stage", note)

    def test_given_an_unrelated_skill_when_the_tool_finishes_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNone(mr.moment(skill_event("flagrare:design-review"), d, s))

    def test_given_a_pr_merge_command_when_it_finishes_then_asks_to_record_the_launch_date(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "gh pr merge 42 --squash"}}
            note = mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("record the launch date", note)
            self.assertNotIn("after stage", note)

    def test_given_a_log_entry_appended_from_a_shell_command_when_it_finishes_then_offers_a_past_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "python3 - <<EOF\nopen('contributions.log.md','a')\nEOF"}}
            self.assertIn("past stage", mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"])

    def test_given_a_contributions_log_write_when_it_finishes_then_offers_a_past_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Edit", "tool_input": {"file_path": f"{d}/{CAREER}/contributions.log.md"}}
            self.assertIn("past stage", mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"])

    def test_given_the_same_moment_twice_in_a_session_when_it_finishes_then_the_second_is_silent(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:work-prep", "T-5"), d, s))
            self.assertIsNone(mr.moment(skill_event("flagrare:work-prep", "T-5"), d, s))
            self.assertIsNotNone(mr.moment(skill_event("flagrare:work-prep", "T-6"), d, s))

    def test_given_reminders_turned_off_when_a_moment_happens_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": False}}}))
            self.assertIsNone(mr.moment(skill_event("flagrare:tdd-writer"), d, s))

    def test_given_skipped_work_when_its_moment_happens_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            skipped = {"id": "typo-fix", "work": {"title": "Fix a typo", "link": "https://tracker.example/T-9", "kind": "ticket"},
                       "stage": "skipped", "skipped_reason": "small fix"}
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([skipped]))
            self.assertIsNone(mr.moment(skill_event("flagrare:work-prep", "https://tracker.example/T-9"), d, s))
            self.assertIsNone(mr.moment(skill_event("flagrare:work-prep", "T-9", sid="s2"), d, s))

    def test_given_no_session_id_when_a_moment_happens_then_still_notes_it(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:tdd-writer", sid=""), d, s))

    def test_given_an_unwritable_state_folder_when_a_moment_happens_then_still_notes_it(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:tdd-writer"), d, "/nonexistent/folder/for/state"))


class CommandLine(unittest.TestCase):
    def test_given_garbage_on_stdin_when_the_moment_hook_runs_then_prints_nothing_and_exits_0(self):
        for text in ["", "not json", "[1, 2]"]:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
                    self.assertEqual(mr.main(["x", "moment"], text, d, "2026-10-16", s), "")
                script = HOOKS / "measure_reminders.py"
                done = subprocess.run([sys.executable, str(script), "moment"], input=text, capture_output=True, text=True)
                self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_given_a_moment_on_stdin_when_the_hook_runs_then_prints_the_json_note(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            out = mr.main(["x", "moment"], json.dumps(skill_event("flagrare:open-pr")), d, "2026-10-16", s)
            self.assertIn("a PR is being opened", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_given_a_scratchpad_in_the_event_when_the_hook_runs_then_keeps_its_once_per_session_list_there(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as fallback, tempfile.TemporaryDirectory() as pad:
            event = {**skill_event("flagrare:open-pr"), "scratchpad_dir": pad}
            mr.main(["x", "moment"], json.dumps(event), d, "2026-10-16", fallback)
            self.assertEqual([p.name for p in Path(pad).iterdir()], ["flagrare-measure-s1.json"])
            self.assertEqual(list(Path(fallback).iterdir()), [])

class Registration(unittest.TestCase):
    def test_given_the_plugin_hooks_file_when_read_then_both_reminders_are_registered_on_an_existing_script(self):
        config = json.loads((HOOKS / "hooks.json").read_text())
        commands = {}
        for event, groups in config["hooks"].items():
            for group in groups:
                for hook in group.get("hooks", []):
                    if "measure_reminders.py" in hook.get("command", ""):
                        commands[event] = (group.get("matcher"), hook["command"])
        self.assertEqual(set(commands), {"SessionStart", "PostToolUse", "UserPromptExpansion"})
        self.assertIn("tdd-writer", commands["UserPromptExpansion"][0])
        self.assertTrue(commands["UserPromptExpansion"][1].endswith("measure_reminders.py expansion"))
        self.assertEqual(commands["SessionStart"][0], "startup|resume")
        self.assertEqual(commands["PostToolUse"][0], "Skill|Bash|Write|Edit")
        self.assertTrue(commands["SessionStart"][1].endswith("measure_reminders.py session-start"))
        self.assertTrue(commands["PostToolUse"][1].endswith("measure_reminders.py moment"))
        self.assertTrue((HOOKS / "measure_reminders.py").is_file())

class ReviewFixes(unittest.TestCase):
    def test_given_a_typed_slash_command_when_it_expands_then_prints_a_plain_note_for_claude(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "hook_event_name": "UserPromptExpansion", "command_name": "tdd-writer", "command_args": ["T-5"]}
            out = mr.main(["x", "expansion"], json.dumps(event), d, "2026-10-16", s)
            self.assertIn("a TDD is being written", out)
            self.assertFalse(out.startswith("{"))

    def test_given_commands_that_only_mention_a_pr_when_they_finish_then_say_nothing(self):
        for command in ["git log --grep 'gh pr merge'", "gh pr merge --help", "gh pr merge 42 --auto",
                        "git commit -m 'fix the gh pr create flow'", "tail -5 ~/.claude/skills/flagrare/career/contributions.log.md"]:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
                self.assertIsNone(mr.moment({"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": command}}, d, s))

    def test_given_a_merge_after_other_commands_when_it_finishes_then_still_notes_it(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "cd repo && gh pr merge 42 --squash"}}
            self.assertIsNotNone(mr.moment(event, d, s))

    def test_given_a_log_append_with_shell_redirect_when_it_finishes_then_offers_a_past_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "echo '- 2026-10-16 | x | y' >> career/contributions.log.md"}}
            self.assertIn("past stage", mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"])

    def test_given_bets_waiting_for_launch_when_a_pr_merges_then_the_note_names_them_and_the_skill(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            waiting = measurement(launch_date=None, checks=[])
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([waiting]))
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "gh pr merge 42 --squash"}}
            note = mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("/flagrare:measure-impact", note)
            self.assertIn("Reorder button for Acme Pizza (acme-reorder)", note)

    def test_given_a_skipped_ticket_when_a_longer_key_starts_with_it_then_still_notes(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            skipped = {"id": "typo-fix", "work": {"title": "Fix a typo", "link": "https://tracker.example/T-9", "kind": "ticket"},
                       "stage": "skipped", "skipped_reason": "small fix"}
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([skipped]))
            self.assertIsNotNone(mr.moment(skill_event("flagrare:work-prep", "T-91"), d, s))

    def test_given_two_different_log_entries_in_a_session_when_written_then_each_gets_a_note(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            path = f"{d}/{CAREER}/contributions.log.md"
            first = {"session_id": "s1", "tool_name": "Edit", "tool_input": {"file_path": path, "new_string": "- win one"}}
            second = {"session_id": "s1", "tool_name": "Edit", "tool_input": {"file_path": path, "new_string": "- win two"}}
            self.assertIsNotNone(mr.moment(first, d, s))
            self.assertIsNone(mr.moment(first, d, s))
            self.assertIsNotNone(mr.moment(second, d, s))

    def test_given_reminders_set_to_the_string_false_when_a_moment_happens_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": "false"}}}))
            self.assertIsNone(mr.moment(skill_event("flagrare:tdd-writer"), d, s))

    def test_given_the_library_fails_to_load_when_the_hook_runs_then_prints_nothing(self):
        original = mr._lib
        def broken():
            raise ImportError("broken")
        mr._lib = broken
        try:
            with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
                self.assertEqual(mr.main(["x", "moment"], json.dumps(skill_event("flagrare:tdd-writer")), d, "2026-10-16", s), "")
                self.assertEqual(mr.main(["x", "session-start"], "", d, "2026-10-16", s), "")
        finally:
            mr._lib = original


if __name__ == "__main__":
    unittest.main()
