from __future__ import annotations
import json
import shutil
import subprocess
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "hooks"


def run(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(HOOKS / script)], input=json.dumps(payload), capture_output=True, text=True)


def context(out: subprocess.CompletedProcess) -> str:
    data = json.loads(out.stdout)
    return data["hookSpecificOutput"]["hookEventName"] + ": " + data["hookSpecificOutput"]["additionalContext"]


@unittest.skipUnless(shutil.which("jq"), "the shell hooks need jq")
class PostToolUseHooksReachClaude(unittest.TestCase):
    def test_given_wrap_up_loads_when_the_hook_runs_then_claude_is_told_what_follows_once_it_finishes(self):
        out = run("post_skill_chain.sh", {"tool_name": "Skill", "tool_input": {"skill": "flagrare:wrap-up"}})
        self.assertEqual(out.returncode, 0)
        text = context(out)
        self.assertTrue(text.startswith("PostToolUse: "))
        self.assertIn("When /flagrare:wrap-up finishes", text)
        self.assertIn("/flagrare:implementation-review", text)

    def test_given_staleness_audit_loads_when_the_hook_runs_then_claude_is_told_about_release_check(self):
        self.assertIn("/flagrare:release-check", context(run("post_skill_chain.sh", {"tool_input": {"skill": "flagrare:staleness-audit"}})))

    def test_given_any_other_skill_when_the_hook_runs_then_it_says_nothing(self):
        out = run("post_skill_chain.sh", {"tool_input": {"skill": "flagrare:open-pr"}})
        self.assertEqual((out.returncode, out.stdout, out.stderr), (0, "", ""))

    def test_given_a_web_fetch_when_the_research_hook_runs_then_claude_gets_the_reminder(self):
        out = run("research_catalog_reminder.sh", {"tool_name": "WebFetch"})
        self.assertEqual(out.returncode, 0)
        self.assertIn("/flagrare:research-catalog", context(out))


if __name__ == "__main__":
    unittest.main()
