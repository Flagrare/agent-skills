"""Index the user's own copy of the ASD-STE100 dictionary and look words up in it.

Commands:
  setup <file.pdf|file.txt>   extract the text and save the settings
  start-at <line>             skip everything before this line of the text (the intro)
  status                      print the settings as JSON
  lookup <word>...            print the dictionary entries for each word
  lookup --from <file>        same, for every distinct word in a file
  glossary add <term>...      add project terms the dictionary doesn't have
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

INSTALL_HINTS = (
    "No PDF text extractor found. Install one, then run setup again:\n"
    "  macOS:          brew install poppler\n"
    "  Debian/Ubuntu:  sudo apt install poppler-utils\n"
    "  Fedora:         sudo dnf install poppler-utils\n"
    "  Windows:        choco install poppler   (or: scoop install poppler)\n"
    "  Any OS:         python3 -m pip install --user pypdf"
)
EXIT_NO_EXTRACTOR = 2
MIN_DICTIONARY_LINES = 50
MIN_STEM_LENGTH = 2
DEFAULT_CONTEXT_LINES = 2
DEFAULT_ENTRY_LIMIT = 3
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
SUFFIXES = ("ies", "ied", "es", "s", "ed", "ing", "er", "est", "ly")
SILENT_E_SUFFIXES = ("ed", "ing", "er", "est", "es")
VOWELS = set("aeiou")
VERB_HEADWORD = re.compile(r"^[A-Za-z][\w'.-]*(?: [\w'.-]+)* ?\(v\)", re.IGNORECASE)
VERB_FORM = re.compile(r"^[A-Za-z'-]+,?(\s{2,}|$)")
MAX_VERB_FORMS = 6


class SetupError(Exception):
    pass


def skill_dir(home):
    return os.path.join(home, ".claude", "skills", "flagrare", "controlled-english")


def settings_path(home):
    return os.path.join(skill_dir(home), "settings.json")


def default_paths(home):
    base = skill_dir(home)
    return {
        "dictionary_text": os.path.join(base, "dictionary.txt"),
        "glossary": os.path.join(base, "glossary.txt"),
        "conventions": os.path.join(base, "conventions.md"),
    }


def load_settings(home):
    try:
        with open(settings_path(home), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_settings(home, settings):
    os.makedirs(skill_dir(home), exist_ok=True)
    with open(settings_path(home), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            # pdftotext starts each page with a form feed. splitlines() would count it as a line break and
            # shift every line number away from what grep shows, so drop it and split on newlines only.
            return f.read().replace("\f", "").split("\n")
    except FileNotFoundError:
        return []


def extract(source, target):
    """Returns the tool name, or None when no extractor is installed."""
    if source.lower().endswith(".txt"):
        shutil.copyfile(source, target)
        return "copy"
    if shutil.which("pdftotext"):
        try:
            subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", source, target], check=True, capture_output=True)
        except subprocess.CalledProcessError as error:
            raise SetupError(f"pdftotext could not read {source}: {error.stderr.decode(errors='replace').strip()}")
        return "pdftotext -layout"
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(source)
        with open(target, "w", encoding="utf-8") as out:
            for page in reader.pages:
                out.write((page.extract_text(extraction_mode="layout") or "") + "\n")
    except Exception as error:
        raise SetupError(f"pypdf could not read {source}: {error}")
    return "pypdf"


def cmd_setup(args):
    source = os.path.abspath(os.path.expanduser(args.source))
    if not os.path.isfile(source):
        sys.exit(f"File not found: {source}")
    os.makedirs(skill_dir(args.home), exist_ok=True)
    settings = {**default_paths(args.home), **load_settings(args.home)}
    target = settings["dictionary_text"]
    # Extract to a scratch file first: a bad source must not replace a dictionary that works.
    fd, scratch = tempfile.mkstemp(dir=skill_dir(args.home), suffix=".txt")
    os.close(fd)
    try:
        tool = extract(source, scratch)
        if tool is None:
            print(INSTALL_HINTS, file=sys.stderr)
            sys.exit(EXIT_NO_EXTRACTOR)
        lines = len(read_lines(scratch))
        if lines < MIN_DICTIONARY_LINES:
            sys.exit(f"Only {lines} lines came out of {source}. It may be a scanned PDF or the wrong file.")
        os.replace(scratch, target)
    except SetupError as error:
        sys.exit(str(error))
    finally:
        if os.path.exists(scratch):
            os.remove(scratch)
    if settings.get("source") != source:
        settings.pop("starts_at_line", None)
    settings.update(
        {"source": source, "extracted_with": tool, "extracted_at": datetime.date.today().isoformat(), "lines": lines}
    )
    save_settings(args.home, settings)
    print(json.dumps(settings, indent=2))


def cmd_start_at(args):
    settings = load_settings(args.home)
    if not os.path.isfile(settings.get("dictionary_text", "")):
        sys.exit("No dictionary configured. Run setup first.")
    settings["starts_at_line"] = args.line
    save_settings(args.home, settings)
    print(f"Lookups start at line {args.line} of {settings['dictionary_text']}")


def cmd_status(args):
    settings = load_settings(args.home)
    settings["configured"] = os.path.isfile(settings.get("dictionary_text", ""))
    settings["conventions_written"] = os.path.isfile(settings.get("conventions", ""))
    print(json.dumps(settings, indent=2))


def candidates(word):
    word = word.lower()
    forms = [word]
    for suffix in SUFFIXES:
        if not word.endswith(suffix) or len(word) - len(suffix) < MIN_STEM_LENGTH:
            continue
        stem = word[: -len(suffix)]
        if suffix in ("ies", "ied"):
            forms.append(stem + "y")
            break
        forms.append(stem)
        if suffix in SILENT_E_SUFFIXES:
            forms.append(stem + "e")
        if len(stem) > MIN_STEM_LENGTH and stem[-1] == stem[-2] and stem[-1] not in VOWELS:
            forms.append(stem[:-1])
    return list(dict.fromkeys(forms))


def headword_above(lines, i):
    """For a verb form listed under its headword ("GAVE," under "GIVE (v),"), the headword's line."""
    if not VERB_FORM.match(lines[i]):
        return i
    for j in range(i - 1, max(i - 1 - MAX_VERB_FORMS, -1), -1):
        if VERB_HEADWORD.match(lines[j]):
            return j
        if not VERB_FORM.match(lines[j]):
            break
    return i


def entries(lines, word, context, limit):
    """Entries for the word come first, then verb forms under their headword, then any other line starting with it."""
    starts = re.compile(r"^\s*" + re.escape(word) + r"(?![\w-])", re.IGNORECASE)
    labelled = re.compile(r"^\s*" + re.escape(word) + r"\s*\(", re.IGNORECASE)
    matches = [(i, headword_above(lines, i)) for i, line in enumerate(lines) if starts.match(line)]
    matches.sort(key=lambda m: 0 if labelled.match(lines[m[0]]) else 1 if m[1] != m[0] else 2)
    found = {}
    for i, start in matches:
        if start not in found:
            found[start] = "\n".join(lines[start : i + 1 + context]).rstrip()
        if len(found) == limit:
            break
    return list(found.values())


def glossary_words(path):
    return {w.lower() for term in read_lines(path) for w in WORD.findall(term)}


def cmd_lookup(args):
    settings = load_settings(args.home)
    if not os.path.isfile(settings.get("dictionary_text", "")):
        sys.exit("No dictionary configured. Run: ste_dictionary.py setup <path-to-ASD-STE100.pdf>")
    lines = read_lines(settings["dictionary_text"])[max(settings.get("starts_at_line", 1) - 1, 0) :]
    glossary = glossary_words(settings.get("glossary", ""))
    words = list(args.words)
    if args.source:
        try:
            with open(args.source, encoding="utf-8", errors="replace") as f:
                words += WORD.findall(f.read())
        except FileNotFoundError:
            sys.exit(f"File not found: {args.source}")
    report = []
    for word in dict.fromkeys(w.lower() for w in words):
        if word in glossary:
            report.append({"word": word, "status": "glossary"})
            continue
        for form in candidates(word):
            found = entries(lines, form, args.context, args.limit)
            if found:
                report.append({"word": word, "status": "entry", "matched": form, "entries": found})
                break
        else:
            report.append({"word": word, "status": "check"})
    print(json.dumps(report, indent=2))


def cmd_glossary(args):
    settings = {**default_paths(args.home), **load_settings(args.home)}
    path = settings["glossary"]
    existing = {t.strip().lower() for t in read_lines(path) if t.strip()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    needs_newline = os.path.isfile(path) and os.path.getsize(path) > 0 and not open(path, "rb").read().endswith(b"\n")
    with open(path, "a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        for term in args.terms:
            if term.lower() not in existing:
                f.write(term + "\n")
                existing.add(term.lower())
    save_settings(args.home, {**load_settings(args.home), "glossary": path})
    print(f"{len(existing)} terms in {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--home", default=os.path.expanduser("~"))
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup")
    setup.add_argument("source")
    setup.set_defaults(func=cmd_setup)
    start_at = commands.add_parser("start-at")
    start_at.add_argument("line", type=int)
    start_at.set_defaults(func=cmd_start_at)
    commands.add_parser("status").set_defaults(func=cmd_status)
    lookup = commands.add_parser("lookup")
    lookup.add_argument("words", nargs="*")
    lookup.add_argument("--from", dest="source")
    lookup.add_argument("--context", type=int, default=DEFAULT_CONTEXT_LINES, help="lines shown after each entry line")
    lookup.add_argument("--limit", type=int, default=DEFAULT_ENTRY_LIMIT, help="entries shown per word")
    lookup.set_defaults(func=cmd_lookup)
    glossary = commands.add_parser("glossary")
    glossary.add_argument("action", choices=["add"])
    glossary.add_argument("terms", nargs="+")
    glossary.set_defaults(func=cmd_glossary)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
