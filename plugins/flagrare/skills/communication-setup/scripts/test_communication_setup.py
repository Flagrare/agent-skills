"""Run: python3 -m unittest discover -s plugins/flagrare/skills/communication-setup/scripts"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    "name": "Ana",
    "style_name": "Ana",
    "rules": ["Answer first.", "Plain words."],
    "max_lines": 3,
    "max_words": 40,
    "depth_words": ["explain"],
}
OTHER_HOOK = {"hooks": [{"type": "command", "command": "python3 /somewhere/else.py"}]}


def run(*args, stdin=None, env=None):
    return subprocess.run([sys.executable, *args], input=stdin, capture_output=True, text=True, env=env, check=True)


class CommunicationSetupTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.claude = os.path.join(self.home, ".claude")
        os.makedirs(self.claude)
        self.settings_path = os.path.join(self.claude, "settings.json")
        with open(self.settings_path, "w") as f:
            json.dump({"outputStyle": "Explanatory", "hooks": {"Stop": [OTHER_HOOK]}}, f)
        self.config_path = os.path.join(self.home, "config.json")
        with open(self.config_path, "w") as f:
            json.dump(CONFIG, f)
        self.env = {**os.environ, "HOME": self.home}

    def setup(self, *args):
        return run(os.path.join(HERE, "setup.py"), *args, "--home", self.home)

    def settings(self):
        with open(self.settings_path) as f:
            return json.load(f)

    def hook(self, script, payload):
        return run(os.path.join(self.claude, "hooks", "communication-setup", script),
                   stdin=json.dumps(payload), env=self.env).stdout

    def transcript(self, prompt):
        path = os.path.join(self.home, "t.jsonl")
        with open(path, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"content": prompt}}) + "\n")
        return path

    def test_install_activates_the_style_and_keeps_other_hooks(self):
        self.setup("install", self.config_path)
        settings = self.settings()
        self.assertEqual(settings["outputStyle"], "Ana")
        self.assertIn(OTHER_HOOK, settings["hooks"]["Stop"])
        self.assertIn("UserPromptSubmit", settings["hooks"])
        with open(os.path.join(self.claude, "output-styles", "Ana.md")) as f:
            style = f.read()
        self.assertIn("keep-coding-instructions: true", style)
        self.assertIn("- Answer first.", style)

    def test_installing_twice_registers_each_hook_once(self):
        self.setup("install", self.config_path)
        self.setup("install", self.config_path)
        commands = [h["command"] for g in self.settings()["hooks"]["Stop"] for h in g["hooks"]]
        self.assertEqual(sum("communication-setup" in c for c in commands), 1)

    def test_remove_restores_the_previous_style_and_leaves_other_hooks(self):
        self.setup("install", self.config_path)
        self.setup("install", self.config_path)
        self.setup("remove")
        self.assertEqual(self.settings(), {"outputStyle": "Explanatory", "hooks": {"Stop": [OTHER_HOOK]}})
        self.assertFalse(os.path.exists(os.path.join(self.claude, "output-styles", "Ana.md")))
        self.assertFalse(os.path.exists(os.path.join(self.claude, "communication-setup.json")))

    def reply(self, n):
        return "\n".join(f"Line {i} of a reply." for i in range(n))

    def test_a_reply_a_little_long_is_not_blocked_but_the_next_message_says_so_once(self):
        self.setup("install", self.config_path)
        out = self.hook("reply_length.py", {"last_assistant_message": self.reply(5),
                                            "transcript_path": self.transcript("yes")})
        self.assertEqual(out, "")
        first = json.loads(self.hook("reply_reminder.py", {"prompt": "ok"}))
        self.assertIn("Your last reply ran long (5 lines", first["hookSpecificOutput"]["additionalContext"])
        second = json.loads(self.hook("reply_reminder.py", {"prompt": "ok"}))
        self.assertNotIn("ran long", second["hookSpecificOutput"]["additionalContext"])

    def test_a_reply_far_over_the_limit_is_blocked_once_then_allowed(self):
        self.setup("install", self.config_path)
        payload = {"last_assistant_message": self.reply(10), "transcript_path": self.transcript("yes")}
        self.assertEqual(json.loads(self.hook("reply_length.py", payload))["decision"], "block")
        self.assertEqual(self.hook("reply_length.py", {**payload, "stop_hook_active": True}), "")

    def test_a_reply_within_the_limit_leaves_no_note(self):
        self.setup("install", self.config_path)
        self.hook("reply_length.py", {"last_assistant_message": self.reply(2), "transcript_path": self.transcript("yes")})
        out = json.loads(self.hook("reply_reminder.py", {"prompt": "ok"}))
        self.assertNotIn("ran long", out["hookSpecificOutput"]["additionalContext"])

    def test_drafts_and_requests_for_depth_are_not_counted(self):
        self.setup("install", self.config_path)
        draft = "Here it is:\n" + "\n".join("> draft line" for _ in range(30)) + "\nSave it?"
        self.assertEqual(self.hook("reply_length.py", {"last_assistant_message": draft,
                                                       "transcript_path": self.transcript("yes")}), "")
        self.assertEqual(self.hook("reply_length.py", {"last_assistant_message": self.reply(10),
                                                       "transcript_path": self.transcript("explain it")}), "")

    def test_the_reminder_carries_the_rules(self):
        self.setup("install", self.config_path)
        out = json.loads(self.hook("reply_reminder.py", {"prompt": "hi"}))
        self.assertIn("1) Answer first.", out["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
