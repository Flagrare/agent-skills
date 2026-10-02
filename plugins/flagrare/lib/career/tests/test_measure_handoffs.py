from __future__ import annotations
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / "skills"


class Handoffs(unittest.TestCase):
    def check(self, wired: dict[str, str]) -> None:
        for name, phrase in wired.items():
            with self.subTest(skill=name):
                text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(phrase, text)

    def test_given_the_skills_used_before_building_when_read_then_each_hands_off_to_measure_impact(self):
        self.check({
            "tdd-writer": "called by /flagrare:tdd-writer",
            "work-prep": "Set the bet with `/flagrare:measure-impact`",
            "intake": "called by /flagrare:work-prep",
            "atdd-plan": "bet from `/flagrare:measure-impact`",
        })


if __name__ == "__main__":
    unittest.main()
