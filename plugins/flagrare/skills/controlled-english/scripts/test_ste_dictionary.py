"""Run: python3 -m unittest discover -s plugins/flagrare/skills/controlled-english/scripts

The dictionary here is made up. No text from ASD-STE100 may appear in this repo.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "ste_dictionary.py")

INTRO = ["Glorp is how this made-up intro starts a line."] + ["Front matter line"] * 59
ENTRIES = [
    "GLORP (v)          To make a thing tidy.        GLORP THE DESK.",
    "                   Second line of glorp.",
    "blint (v)          GLORP                        GLORP THE DESK.",
    "                   (Not: Blint the desk.)",
    "WOMBLE (n)         A small round thing.         THE WOMBLE IS BLUE. A FLONK IS NEAR.",
    "ZAP (v),           To hit fast.                 ZAP THE FLY.",
    "\fZAPS,",
    "ZOPPED,            the fast way                 THEN ZAP IT AGAIN.",
    "ZOPPED",
    "UBE (v)            To put to work.              UBE THE TOOL.",
    "SOME (adj)         Not all.                     SOME OF THE TOOLS.",
    "UPP,               spill-over text of a cell",
    "SKRY (v)           To look far.                 SKRY THE HILL.",
]
FAKE_DICTIONARY = "\n".join(INTRO[:30]) + "\n\f" + "\n".join(INTRO[30:] + ENTRIES)
FIRST_ENTRY_LINE = len(INTRO) + 1


class SteDictionaryTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home)
        self.source = self.write("standard.txt", FAKE_DICTIONARY)

    def write(self, name, text):
        path = os.path.join(self.home, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def run_script(self, *args, check=True, env=None):
        return subprocess.run(
            [sys.executable, SCRIPT, "--home", self.home, *args], capture_output=True, text=True, check=check, env=env
        )

    def lookup(self, *args):
        return {r["word"]: r for r in json.loads(self.run_script("lookup", *args).stdout)}

    def status(self):
        return json.loads(self.run_script("status").stdout)

    def test_status_says_not_configured_before_setup(self):
        self.assertEqual(self.status(), {"configured": False, "conventions_written": False})

    def test_lookup_before_setup_tells_the_user_to_run_setup(self):
        result = self.run_script("lookup", "glorp", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Run: ste_dictionary.py setup", result.stderr)

    def test_setup_reports_configured(self):
        self.run_script("setup", self.source)
        self.assertTrue(self.status()["configured"])

    def test_lookup_returns_the_entry_with_the_lines_after_it(self):
        self.run_script("setup", self.source)
        entry = self.lookup("glorp")["glorp"]
        self.assertEqual(entry["status"], "entry")
        self.assertIn("Second line of glorp.", entry["entries"][0])

    def test_entry_lines_come_before_prose_that_starts_with_the_same_word(self):
        self.run_script("setup", self.source)
        self.assertTrue(self.lookup("glorp")["glorp"]["entries"][0].startswith("GLORP (v)"))

    def test_start_at_skips_the_intro(self):
        self.run_script("setup", self.source)
        self.run_script("start-at", str(FIRST_ENTRY_LINE))
        self.assertEqual(len(self.lookup("glorp")["glorp"]["entries"]), 1)

    def test_irregular_verb_form_returns_its_headword_entry_once_across_a_page_break(self):
        self.run_script("setup", self.source)
        found = self.lookup("zopped")["zopped"]["entries"]
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith("ZAP (v),"))

    def test_line_under_a_non_verb_entry_is_not_treated_as_a_verb_form(self):
        self.run_script("setup", self.source)
        self.assertTrue(self.lookup("upp")["upp"]["entries"][0].startswith("UPP,"))

    def test_start_at_line_numbers_match_grep_even_across_page_breaks(self):
        self.run_script("setup", self.source)
        self.run_script("start-at", str(FIRST_ENTRY_LINE))
        self.assertEqual(self.lookup("front")["front"]["status"], "check")

    def test_lookup_ignores_case(self):
        self.run_script("setup", self.source)
        self.assertEqual(self.lookup("GLORP")["glorp"]["status"], "entry")

    def test_unapproved_word_returns_its_entry_with_the_alternative(self):
        self.run_script("setup", self.source)
        self.assertIn("Not: Blint the desk.", self.lookup("blint")["blint"]["entries"][0])

    def test_inflected_forms_find_the_base_word(self):
        self.run_script("setup", self.source)
        expected = {"glorped": "glorp", "glorps": "glorp", "zapped": "zap", "zapping": "zap",
                    "ubed": "ube", "ubing": "ube", "skried": "skry", "skries": "skry"}
        found = self.lookup(*expected)
        self.assertEqual({w: found[w]["matched"] for w in expected}, expected)

    def test_word_found_only_inside_other_lines_is_marked_check(self):
        self.run_script("setup", self.source)
        self.assertEqual(self.lookup("flonk")["flonk"]["status"], "check")

    def test_word_not_in_the_dictionary_is_marked_check_not_wrong(self):
        self.run_script("setup", self.source)
        self.assertEqual(self.lookup("kubernetes")["kubernetes"]["status"], "check")

    def test_glossary_terms_are_accepted_even_over_a_dictionary_entry(self):
        self.run_script("setup", self.source)
        self.run_script("glossary", "add", "Kubernetes", "glorp")
        found = self.lookup("kubernetes", "glorp")
        self.assertEqual([found["kubernetes"]["status"], found["glorp"]["status"]], ["glossary", "glossary"])

    def test_each_word_of_a_multi_word_glossary_term_is_accepted(self):
        self.run_script("setup", self.source)
        self.run_script("glossary", "add", "Billing Portal")
        self.assertEqual(self.lookup("portal")["portal"]["status"], "glossary")

    def test_glossary_add_skips_terms_already_there_in_any_case(self):
        self.run_script("glossary", "add", "Foo", "foo")
        self.assertIn("1 terms", self.run_script("glossary", "add", "FOO").stdout)

    def test_glossary_added_before_setup_survives_setup(self):
        self.run_script("glossary", "add", "Kubernetes")
        self.run_script("setup", self.source)
        self.assertEqual(self.lookup("kubernetes")["kubernetes"]["status"], "glossary")

    def test_lookup_from_a_file_covers_each_distinct_word_once(self):
        self.run_script("setup", self.source)
        draft = self.write("draft.md", "Glorp the womble. Glorp it again.")
        result = json.loads(self.run_script("lookup", "--from", draft).stdout)
        self.assertEqual([r["word"] for r in result], ["glorp", "the", "womble", "it", "again"])

    def test_lookup_from_a_missing_file_says_so(self):
        self.run_script("setup", self.source)
        result = self.run_script("lookup", "--from", os.path.join(self.home, "nope.md"), check=False)
        self.assertIn("File not found", result.stderr)

    def test_setup_with_a_missing_file_says_so(self):
        result = self.run_script("setup", os.path.join(self.home, "nope.pdf"), check=False)
        self.assertIn("File not found", result.stderr)

    def test_setup_rejects_a_file_with_almost_no_text(self):
        result = self.run_script("setup", self.write("scan.txt", "one line"), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scanned PDF", result.stderr)

    def test_a_failed_setup_keeps_the_dictionary_that_worked(self):
        self.run_script("setup", self.source)
        self.run_script("setup", self.write("scan.txt", "one line"), check=False)
        self.assertEqual(self.lookup("glorp")["glorp"]["status"], "entry")

    def test_setup_twice_keeps_the_glossary(self):
        self.run_script("setup", self.source)
        self.run_script("glossary", "add", "Kubernetes")
        self.run_script("setup", self.source)
        self.assertEqual(self.lookup("kubernetes")["kubernetes"]["status"], "glossary")

    def test_pdf_without_an_extractor_shows_install_hints(self):
        blocker = os.path.join(self.home, "blocker")
        os.makedirs(os.path.join(blocker, "pypdf"))
        self.write(os.path.join("blocker", "pypdf", "__init__.py"), "raise ImportError('blocked for the test')")
        env = {**os.environ, "PATH": os.path.join(self.home, "empty-path"), "PYTHONPATH": blocker}
        result = self.run_script("setup", self.write("standard.pdf", "%PDF-1.4"), check=False, env=env)
        self.assertEqual(result.returncode, 2)
        self.assertIn("brew install poppler", result.stderr)


if __name__ == "__main__":
    unittest.main()
