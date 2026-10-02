from __future__ import annotations
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / "skills"
CALL = r"(before|after|past) (<[^>]+>|\S+) (quick|full)( nosave)? called by /flagrare:[a-z-]+"


def read(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def bullet(text: str, start: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(start))


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

    def test_given_the_career_digest_when_read_then_it_has_a_measure_line(self):
        self.check({"career": "**Measure:** check due:"})

    def test_given_the_career_digest_when_a_measure_group_is_empty_then_it_is_left_out(self):
        self.assertIn("omit any empty group", bullet(read("career"), "- **The Measure line**"))


class HandoffSafety(unittest.TestCase):
    def test_given_any_skill_that_runs_measure_impact_when_read_then_it_passes_stage_link_size_and_caller(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r"[Rr]un(?:ning)? `/flagrare:measure-impact`(.{0,160})", text):
                with self.subTest(skill=path.parent.name, at=m.group(0)[:80]):
                    self.assertRegex(m.group(1), r"^ with `" + CALL + "`")

    def test_given_a_called_skill_when_measure_impact_returns_then_it_says_whether_tracking_exists(self):
        text = read("measure-impact")
        self.assertIn("steps 1, 2, 4, 6, 8 and 9", text)
        self.assertIn("whether its tracking exists", bullet(text, "**Called by another skill**"))

    def test_given_opportunity_scan_when_sizing_proposals_then_nothing_is_saved_until_one_is_agreed(self):
        text = read("opportunity-scan")
        self.assertIn("quick nosave called by /flagrare:opportunity-scan", text)
        self.assertNotIn("measure-impact", bullet(text, "- **Keep:**"))
        self.assertIn("quick called by /flagrare:opportunity-scan", bullet(text, "- **Agreed with the manager:**"))

    def test_given_a_logged_win_when_impact_scan_offers_to_measure_then_a_skip_is_one_word_and_recorded(self):
        text = read("impact-scan")
        self.assertIn("Measure it? (yes / skip)", text)
        self.assertIn("measurements.py skip", text)

    def test_given_intake_called_by_work_prep_when_handing_off_then_it_measures_before_invoking_atdd_plan(self):
        para = bullet(read("intake"), "If invoked through `/flagrare:work-prep`")
        self.assertIn("called by /flagrare:work-prep", para)
        self.assertLess(para.index("called by /flagrare:work-prep"), para.index("invoke `/flagrare:atdd-plan`"))


if __name__ == "__main__":
    unittest.main()
