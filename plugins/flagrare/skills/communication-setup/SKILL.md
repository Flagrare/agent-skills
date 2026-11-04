---
name: communication-setup
description: "Set up, change or remove how Claude talks to you: a custom output style with your reply rules, a reminder of those rules on every message, and a Stop hook that blocks replies longer than you want and makes Claude rewrite them. Use when the user says Claude's replies are too long, exhausting, hard to skim, full of process narration or caveats, 'you make me work for the information', 'talk to me shorter', 'communication setup', 'set up how you talk to me', or asks to remove or undo it ('remove communication setup', 'go back to normal replies')."
---

# Communication setup

Memory notes and CLAUDE.md rules about tone fade in long sessions. This skill enforces them with three pieces, from weakest to strongest:

1. **An output style.** It goes into the system prompt and survives compaction, so it outranks CLAUDE.md. It sets the base voice.
2. **A reminder on every message** (UserPromptSubmit hook). It puts the rules next to each message the user sends, so they stay in view.
3. **A length check** (Stop hook). It blocks a reply that runs past the limit and makes Claude rewrite it. It skips `>` quoted drafts and code blocks, lets the rewrite through so it never loops, and allows any length when the user's message asks for depth ("explain", "details", "full").

Everything lives in `~/.claude` and applies to every project. `scripts/setup.py` (next to this file) installs and removes it. It backs up `settings.json` to `settings.json.bak` before every change, and it only touches its own entries.

## Install or change

**1. Check what's there.** Run `python3 <skill>/scripts/setup.py status`. If it's installed, start from the current config at `~/.claude/communication-setup.json`.

**2. Interview, briefly.** Ask only what you can't infer from the conversation, all in one message:
- What tires them: length, process narration, caveats, too many questions, jargon, convoluted phrasing.
- The reply limit. The default is about 5 lines of prose and a hard block over 8 lines or 120 words.
- Words that mean "go long" for them, in every language they use.
- One real reply of yours they found tiring, if there is one. It becomes the bad example.

**3. Write the config** to a temp file and show it to the user in a few lines before installing:

```json
{
  "name": "Ana",
  "style_name": "Ana",
  "description": "Short, answer-first replies in plain words for Ana, who skims.",
  "about": "Ana skims. Long replies tire her, and she ends up skipping them.",
  "rules": [
    "Answer first, in one or two lines.",
    "About 5 lines outside quoted drafts, unless she asks for depth.",
    "No narration of what you checked, ran or read. Only the result and what you need from her.",
    "No caveats she didn't ask for.",
    "Plain words, said the way you'd say them to a coworker.",
    "At most one question, at the end, yes/no when possible."
  ],
  "max_lines": 8,
  "max_words": 120,
  "depth_words": ["explain", "details", "full", "everything", "walk me through"],
  "example_bad": "a real tiring reply, trimmed",
  "example_good": "the same answer in two lines"
}
```

Only `style_name` and `rules` are required. Write the rules themselves in plain, short sentences: they are what Claude reads every turn.

**4. Install:** `python3 <skill>/scripts/setup.py install <config.json>`. Writing to `~/.claude/settings.json` from a sandboxed Bash needs the sandbox off for that one command.

**5. Tell the user** what changed, in two lines: the style name and the limit. Mention that the style applies from the next session, while the hooks apply right away. Mention that saying "remove communication setup" undoes it.

If they had their own hand-made hook or style for the same purpose, offer to remove it so the rules don't run twice.

## Remove

Run `python3 <skill>/scripts/setup.py remove`. It deletes its hooks, style and config, restores the output style the user had before the first install, and leaves every other hook alone. Then confirm in one line.

## Tuning

- **The hook blocks a reply that should have been long.** Add the user's word for it to `depth_words` and reinstall. Don't raise the limit for one case.
- **Replies are still long but under the limit.** Lower `max_lines` or `max_words`.
- **Rewrites keep coming back long.** The Stop hook lets the second attempt through with a warning, on purpose. Tighten the rules text instead of adding retries.

## Anti-patterns

- **Installing without showing the config.** The rules speak for the user, so the user approves them.
- **Long rules.** A rules list the user would find tiring to read defeats the point. Keep each rule to one plain sentence.
- **Counting drafts.** Drafts are what the user will send, so their length is the user's call. The hook already skips `>` quotes; keep drafts in them.

## Cross-references

- `/flagrare:write-docs`, "Say it plainly": the same plain-wording rule for documents.
- `/flagrare:editorial-pass`, which flags convoluted phrasing in documents.
