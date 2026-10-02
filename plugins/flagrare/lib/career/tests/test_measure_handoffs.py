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


    def test_given_the_shipping_and_scans_skills_when_read_then_each_hands_off_to_measure_impact(self):
        self.check({
            "open-pr": "how we'll know it worked",
            "measure-impact": "`nosave`",
            "opportunity-scan": "called by /flagrare:opportunity-scan",
            "impact-scan": "called by /flagrare:impact-scan",
        })

    def test_given_the_write_ups_skills_when_read_then_each_leads_with_measured_results(self):
        self.check({
            "brag-doc": "### 8b. Measured results",
            "impact-timeline": "**saved measurements**",
            "promotion": "results saved by `/flagrare:measure-impact`",
        })

if __name__ == "__main__":
    unittest.main()
