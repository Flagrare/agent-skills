---
name: controlled-english
description: Rewrite or check English that a machine or a non-native reader must parse with no one to ask, using the rules of ASD-STE100 Simplified Technical English and, when the user has their own copy, its dictionary. For tool and function descriptions, error messages, system prompts, agent instructions, procedures, runbook steps, safety text and anything that goes to translation. Use when the user says "STE", "STE100", "Simplified Technical English", "controlled English", "controlled language", "make this unambiguous", "so an agent can't misread it", "check this against STE", or asks to set up the STE dictionary. Not for chat replies, marketing or creative copy.
---

# Controlled English

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. See `/flagrare:write-docs`.

ASD-STE100 is the controlled language the aerospace industry uses so that maintenance technicians can't misread an instruction. It removes the two biggest sources of misreading: words with more than one meaning, and sentences with more than one possible structure. An agent that parses a tool description or an error message has the same problem as the technician, so the same discipline helps it.

This skill is unofficial. It is not affiliated with, approved by or certified by ASD or the STE Maintenance Group, and its output is not proof of compliance. ASD-STE100 is a registered trademark of ASD. The standard itself stays the reference, and a person reviews anything where compliance matters.

## Settings

Everything user-specific lives in `~/.claude/skills/flagrare/controlled-english/`, outside the plugin:

- `settings.json`: where the user's copy of the standard is, and where its extracted text, glossary and conventions are.
- `dictionary.txt`: text extracted from the user's own copy. It stays on this machine, and only the entries a lookup prints reach the session.
- `conventions.md`: how this issue of the dictionary marks approved words, written once at setup.
- `glossary.txt`: project terms the dictionary doesn't have, one per line.

The script is `scripts/ste_dictionary.py` next to this file. At the start of every run, call `python3 <skill>/scripts/ste_dictionary.py status`. If `configured` is true, use dictionary mode. If `conventions_written` is false, redo setup step 5 before any lookup. If `configured` is false, run setup once (below), or continue in rules-only mode when the user wants to wait.

### Setup

The dictionary is free, but ASD sends it on request. Make this fast:

1. **Send the user the request form.** Give this direct link: [ASD-STE100 request form](https://forms.gle/7gqWUtj2UK2CBTBv5). If it no longer opens, use the [official downloads page](https://www.asd-ste100.org/STE_downloads.html) and its "Fill in the request form" button. Say it takes about a minute and that ASD emails the PDF. Never fill in the form for the user.
2. **Offer to start now.** Rules-only mode works while the email is on its way. Say in one line that word checks start once the PDF arrives.
3. **Ask for the PDF's path** when the user has it. If they don't know it, list `~/Downloads/*STE*100*.pdf` and ask which one. Don't guess.
4. **Run** `python3 <skill>/scripts/ste_dictionary.py setup <path>`. If it exits with install hints, show the user the line for their OS and run setup again after they install. If it says almost no text came out, the PDF may be a scan: ask for a different copy.
5. **Write `conventions.md`.** Read the dictionary's own introduction in `dictionary.txt` (how to use the dictionary, before the first entry). Write down, in a few lines, how an approved word looks, how a word that is not approved looks, how the approved alternative is shown, and what the part-of-speech labels mean. Every later lookup relies on this file, so quote the intro's wording for each marker. Then find the line number of the first dictionary entry and run `ste_dictionary.py start-at <line>`, so lookups skip the intro.
6. **Ask for project terms** (optional): product names, technical nouns and verbs the team uses. Add them with `ste_dictionary.py glossary add <term>...`.
7. Tell the user in two lines what you saved and where, then continue with the text they gave you.

The standard is copyrighted. Read it locally for this user, and never copy dictionary entries into a commit, a PR, a shared doc, a chat message to other people or this skill's files. To explain a change, name the approved word.

## Pick the mode

- **Strict:** text a machine or a translator acts on. Tool and function descriptions, error messages, system prompts, agent instructions, procedures, safety text. Apply every rule below and the dictionary pass.
- **Light:** explanations people read, like READMEs, PR descriptions and changelogs. Apply the sentence rules. Skip the dictionary pass, but keep one word for one meaning.

If the user doesn't say, pick from the text type. Don't use this skill for chat replies: a few short style rules do better there than a long rule set, and models game long rule sets by turning every sentence into a bullet.

## The rules

These are the rules that change how text parses, paraphrased. The standard has the full set and its exact wording.

1. **One instruction per sentence.** "Open the file. Read line 3." Not "Open the file and read line 3, then check it."
2. **Short sentences.** At most 20 words in an instruction, 25 in a description. List items count as sentences.
3. **Active voice.** Name who acts: "The tool deletes the file." Use the passive only when the actor is unknown or doesn't matter.
4. **Simple tenses.** Present, past, future and the imperative. Keep a compound form only when it carries meaning ("may have failed", "has finished and the result is ready") and say you kept it.
5. **Keep every hedge.** Never turn "may" into "will", or a guess into a fact.
6. **Plain single verbs for actions.** "Remove", not "take off". "Check the log", not "perform a check of the log". A phrasal verb's meaning isn't the sum of its words.
7. **Noun clusters of three words at most.** Break "request retry backoff limit value" into a phrase with "of" or "for".
8. **Don't drop words.** Keep articles, subjects and verbs, even when the sentence gets longer.
9. **One word for one meaning, every time.** If the text says "delete", it never also says "remove" for the same action.
10. **No semicolons.** Make two sentences.
11. **Lists for steps.** Three or more steps or conditions go in a numbered list. Conditions come before the action: "If the token expired, request a new one."
12. **Technical names stay.** Keep product names, commands, flags and code exactly as they are, and put code in backticks.

## Dictionary pass (Strict, when configured)

1. Save the rewritten text to a temporary file. Run `ste_dictionary.py lookup --from <file>`.
2. Read `conventions.md`, then judge each result:
   - `entry`: read the entry. If the word is approved in the meaning and part of speech you used, keep it. If it isn't, use the approved alternative the entry gives.
   - `glossary`: keep it.
   - `check`: the word has no entry. It may be a valid technical name or technical verb, which the standard allows. Keep it if it is one, and offer to add it to the glossary. Otherwise use a plainer word that has an entry.
3. Look up any replacement word too, so a fix doesn't add a new problem.
4. Don't fail the text on a `check` word. Missing from the dictionary is a question, not an error.

## Output

Give the rewritten text first. Under it, at most five lines:

- The mode, and either "checked against your copy of the dictionary" or "rules only, no dictionary set up".
- Words you kept on purpose that the dictionary doesn't have, and compound tenses you kept for meaning.
- Any meaning you couldn't keep, as a question for the user.

When the user asks why, show a table of before, after and rule. Don't show it unasked.

## Credits

The structural-versus-dictionary split and the two modes build on [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill) (MIT). The warning about chat replies comes from the evals in [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) (MIT). The research is in [the repo's research notes](https://github.com/Flagrare/agent-skills/blob/main/docs/research/2026-11-24-ste100-skills-prior-art.md).
