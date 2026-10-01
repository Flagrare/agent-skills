from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recognition as rec  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
CONFIG = ".claude/skills/flagrare/config.json"


def bonus(i: int, giver: str, value: str, day: str, plus_ones: int = 0) -> dict:
    return {"id": f"b{i}", "created_at": f"{day}T12:00:00Z", "giver": {"full_name": giver, "email": f"{giver.lower()}@example.com"},
            "receivers": [{"full_name": "Jordan Lee"}], "value": value, "hashtag": f"#{value}", "reason_decoded": f"+10 thanks {i}",
            "child_bonuses": [{"giver": {"full_name": f"Peer {n}"}} for n in range(plus_ones)]}


class FakePlatform:
    """Answers like the platform: /users/me, then pages of bonuses filtered by receiver or giver."""

    def __init__(self, received: list[dict], given: list[dict], page: int = 100):
        self.received, self.given, self.page, self.calls = received, given, page, []

    def __call__(self, url: str, token: str) -> dict:
        self.calls.append(url)
        parsed = urlparse(url)
        if parsed.path.endswith("/users/me"):
            return {"success": True, "result": {"full_name": "Jordan Lee", "email": "jordan@example.com", "manager_email": "sam@example.com"}}
        q = parse_qs(parsed.query)
        items = self.received if "receiver_email" in q else self.given
        skip, limit = int(q["skip"][0]), int(q["limit"][0])
        return {"success": True, "result": items[skip:skip + min(limit, self.page)]}


def with_token(home: Path) -> None:
    p = home / ".config/flagrare/bonusly-token"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("token-123\n")


class Fetch(unittest.TestCase):
    def test_given_a_token_when_fetching_then_plans_the_cache_with_received_and_given_newest_first(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            fake = FakePlatform([bonus(1, "Kai", "team-first", "2026-10-01", plus_ones=2)], [bonus(9, "Jordan", "own-the-outcome", "2026-09-20")])
            [a] = rec.plan_fetch(str(home), "2026-10-01", opener=fake)
            data = json.loads(a["content"])
            self.assertTrue(a["path"].endswith(f"{CAREER}/recognition.json"))
            self.assertEqual((data["user"]["email"], data["since"], len(data["received"]), len(data["given"])), ("jordan@example.com", "2025-10-01", 1, 1))
            self.assertEqual(data["received"][0]["plus_ones"], ["Peer 0", "Peer 1"])
            self.assertEqual(data["received"][0]["link"], "https://bonus.ly/bonuses/b1")

    def test_given_more_than_one_page_when_fetching_then_reads_every_page(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            many = [bonus(i, "Kai", "x", "2026-09-01") for i in range(150)]
            fake = FakePlatform(many, [], page=100)
            [a] = rec.plan_fetch(str(home), "2026-10-01", opener=fake)
            self.assertEqual(len(json.loads(a["content"])["received"]), 150)

    def test_given_no_token_when_fetching_then_says_where_to_put_one(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "bonusly-token"):
                rec.plan_fetch(d, "2026-10-01", opener=FakePlatform([], []))

    def test_given_a_custom_token_file_in_config_when_reading_the_token_then_uses_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / CONFIG).parent.mkdir(parents=True, exist_ok=True)
            (home / CONFIG).write_text(json.dumps({"skills": {"career": {"recognition": {"token_file": "~/secrets/rec"}}}}))
            (home / "secrets").mkdir()
            (home / "secrets/rec").write_text("abc")
            self.assertEqual(rec.read_token(str(home)), "abc")

    def test_given_the_platform_refuses_when_fetching_then_raises_with_its_message(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            with self.assertRaisesRegex(RuntimeError, "Unauthorized"):
                rec.plan_fetch(str(home), "2026-10-01", opener=lambda url, token: {"success": False, "message": "Unauthorized"})


class Safety(unittest.TestCase):
    def test_given_a_token_when_fetching_then_the_token_never_appears_in_the_planned_write(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            [a] = rec.plan_fetch(str(home), "2026-10-01", opener=FakePlatform([bonus(1, "Kai", "team-first", "2026-10-01")], []))
            self.assertNotIn("token-123", json.dumps(a))

    def test_given_the_platform_returns_no_email_when_fetching_then_refuses_instead_of_reading_everyones_bonuses(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            opener = lambda url, token: {"success": True, "result": {"full_name": "Jordan Lee", "email": ""} if "users/me" in url else []}
            with self.assertRaisesRegex(RuntimeError, "email"):
                rec.plan_fetch(str(home), "2026-10-01", opener=opener)

    def test_given_recognition_turned_off_when_fetching_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            with_token(home)
            (home / CONFIG).parent.mkdir(parents=True, exist_ok=True)
            (home / CONFIG).write_text(json.dumps({"skills": {"career": {"recognition": {"enabled": False}}}}))
            with self.assertRaisesRegex(ValueError, "turned off"):
                rec.plan_fetch(str(home), "2026-10-01", opener=FakePlatform([], []))


class CleanText(unittest.TestCase):
    def test_given_a_raw_bonus_message_when_cleaning_then_keeps_only_the_thanks(self):
        raw = "@jordan.lee , @sam.rivera and @ana +25 for all the support during the incident! #team-first ![](https://example.com/x.gif)"
        self.assertEqual(rec.clean_text(raw), "for all the support during the incident!")

    def test_given_a_plain_message_when_cleaning_then_leaves_it_alone(self):
        self.assertEqual(rec.clean_text("Thanks for untangling the billing job"), "Thanks for untangling the billing job")


class Summary(unittest.TestCase):
    def test_given_a_cache_when_summarizing_then_ranks_givers_and_counts_values_and_the_last_30_days(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            received = [rec.normalize(b) for b in [
                bonus(1, "Kai", "team-first", "2026-10-01"), bonus(2, "Kai", "own-the-outcome", "2026-09-20"),
                bonus(3, "Ana", "team-first", "2026-06-01")]]
            p = home / CAREER / "recognition.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"fetched_on": "2026-10-01", "received": received, "given": []}))
            s = rec.summary(str(home), "2026-10-01")
            self.assertEqual((s["received"], s["received_last_30_days"], s["given"]), (3, 2, 0))
            self.assertEqual(tuple(s["values"][0]), ("team-first", 2))
            self.assertEqual([(g["name"], g["count"], g["last"]) for g in s["givers"]], [("Kai", 2, "2026-10-01"), ("Ana", 1, "2026-06-01")])

    def test_given_automatic_thanks_when_summarizing_then_counts_them_apart_and_never_as_people(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            person = rec.normalize(bonus(1, "Kai", "team-first", "2026-09-30"))
            birthday = rec.normalize({**bonus(2, "x", "", "2026-09-29"), "giver": {"full_name": "Happy birthday!", "email": "bot+birthday@bonus.ly"}})
            p = home / CAREER / "recognition.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"fetched_on": "2026-10-01", "received": [person, birthday], "given": []}))
            s = rec.summary(str(home), "2026-10-01")
            self.assertEqual((s["received"], s["automatic"], [g["name"] for g in s["givers"]]), (1, 1, ["Kai"]))
            self.assertTrue(birthday["automatic"])

    def test_given_no_cache_when_summarizing_then_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(rec.summary(d, "2026-10-01"), {"has_recognition": False})


if __name__ == "__main__":
    unittest.main()
