---
name: promotion
description: Build and maintain a sourced promotion map for the user's next level. It interviews the user about their target (level, track, cycle, and why), researches how promotions actually work at their company (process, calendar, packet template, the rubric managers rate against), maps the org and who has first-hand knowledge of the user's work, and computes when to talk to their manager. Every fact carries a source and a verified/unverified/inferred status, and conflicting sources are shown, not resolved silently. Writes ~/.claude/skills/flagrare/career/promotion-map.md and .json, which impact-scan, opportunity-scan and career read. Use when the user says "promotion", "promo plan", "how do promotions work here", "when should I talk to my manager about promotion", "who should see my work", "am I ready for senior", "build my promotion map", or "promotion packet" (packet mode). Also trigger when the user asks about career strategy, sponsors, or calibration at their company.
---

# Promotion

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

A promotion is decided in a room the user isn't in, from a written case, by people who mostly don't know them, on a calendar set months ahead. This skill makes those facts visible early: where the user wants to go and why, how the company actually decides, what the rubric asks for, who has first-hand knowledge of their work, and when the key conversations must happen.

It writes a **promotion map**: `promotion-map.md` for the user to read and bring to a 1:1, and `promotion-map.json` with the same facts for the other career skills. The map is local and private. **This skill never posts, sends, or publishes anything.**

## Library

The plugin ships helper scripts at `<plugin root>/lib/career/`. The plugin root is two directories above this skill's base directory. Run each as `python3 <plugin root>/lib/career/<script>.py ...`. They only read and print JSON; this skill writes every file with the Write tool, because a sandboxed shell cannot write under `~/.claude/skills`.

- `career_state.py paths|contributions|plan --home "$HOME"`: file locations, the contributions log (union of old and new locations), and the migration plan.
- `map_schema.py check <map.json> --today YYYY-MM-DD`: errors, missing sections, stale sections (over 90 days), conflicts.
- `deadlines.py --deadline YYYY-MM-DD --today YYYY-MM-DD [--dead START:END ...] [--published]`: when to talk to the manager. `--dead` is optional and repeatable.

The map's shape is in `reference/map-schema.md`, and the markdown layout is in `reference/map-template.md`.

## 1. Load state (every run)

1. Run `career_state.py plan`. Apply each `write` action with the Write tool, reading the target first if it already exists (the Write tool will not overwrite a file it has not read). A `mkdir` action needs no separate step: the folder is created by the first file written into it. Do not write a placeholder map. **Never delete anything.**
2. Read `~/.claude/skills/flagrare/config.json` (top-level identity keys, the `skills.promotion` block) and the existing map, if any. If the config file or the `skills.promotion` block is missing, continue with defaults.
3. No map means a **first run** (section 3). A map whose `map_schema.py check` output lists `missing` sections means an interrupted first run: resume it at the earliest phase whose sections are missing. Otherwise run a **refresh** (section 4), unless the user asks for `packet` mode (section 5).

## 2. Rules for every fact

- **Source, date, status.** Every fact gets a link or quoted location, the date you checked it, and a status: `verified` (read and quoted in the raw source), `unverified` (a summary, snippet or secondhand), or `inferred` (your reasoning).
- **Quote verbatim from the raw source.** Summarizing fetch tools paraphrase. When a quote will be relied on, re-read the raw page (for example the page's JSON or HTML) and confirm the exact words.
- **Show conflicts, never pick silently.** When two sources disagree (an org chart vs a squad directory, a process page vs the ladder file), store both as `alternatives` and tell the user.
- **"Nothing found" is a valid result.** If a step finds nothing, add a concrete question to `manager_questions` instead of guessing. Many companies have no written process.
- **People facts are sensitive.** Only read the user's own interactions. Record who has first-hand context on the user's work, never a ranking of how useful people are.
- **Ask for consent before using the browser** on HR portals or internal sites.

## 3. First run

Tell the user up front: the first run is long, often an hour or more, and it saves after each phase, so it can be stopped and resumed.

**Every save** writes both `promotion-map.json` and `promotion-map.md`, and sets `sections.<name>.checked_at` (today) and `sections.<name>.sources` for every section written in that phase. A section without `checked_at` counts as stale. Phase 1 writes `target`, `process` and `calendar`; Phase 2 writes `rubric`; Phase 3 writes `org`, `people` and `precedent`; Phase 4 writes `packet_readiness` and `manager_questions`. Write each section even when nothing was found (an empty list or object with its `checked_at`), so an empty section is not mistaken for an interrupted run.

### Phase 1: Target, process and calendar
1. **Interview first, before any research.** Ask one question at a time:
   1. Current level and target level.
   2. Track: individual contributor or manager.
   3. Which cycle they're aiming at (come back to this after step 4, once the calendar is known, and propose one).
   4. **Why** they want it, what work they want **more of**, and what they want **less of**.
2. **Look up two facts about the target level:** is it terminal at this company (no expectation of promotion beyond it), and what's the expected time band at the current level? Quote both.
3. **Say what the "why" changes.** A terminal target plus a "peace of mind" why makes the target the finish line. A "money" or "scope" why means planning past it. Write this into the map's section 1.
4. **Find the process, calendar and packet template** in every connected source: wiki, docs, chat announcements, meeting notes, the HR portal (with consent). Also find **how product decisions get made**: the decision document and who usually drives it. Opportunity-scan needs this.
5. Save the map (JSON and markdown) with the `target`, `process`, `calendar` and `sections` entries filled in.

### Phase 2: Rubric gap
1. **Find the artifact managers rate against** (a ladder spreadsheet, a check-in workbook), not prose written about it. Ask the user whether their manager uses a check-in workbook. If prose and artifact disagree, use the artifact and record the mismatch in `rubric.prose_mismatches`.
2. Build one `rubric.rows` entry per behavior: the current-level text, the target-level text, and a stable id (`<area>.<short-slug>`).
3. Mark each row `done`, `partial` or `not_started`, with evidence from `career_state.py contributions`, the user's reviews and work, and prior review notes the user shares.
4. Save.

### Phase 3: Org and who knows your work
1. **Org:** the user's chain, who sits above each team they might land on, and upcoming changes (departures, new leaders, reorgs from meeting notes and announcements). Every person gets a source and a status.
2. **Who knows your work, evidence first, then the user:**
   - Propose people from the user's own interactions (reviews given and received, shared threads, shared meetings), each with evidence links.
   - Ask the user to confirm and correct, and to add what no tool can see, like a former manager or a hackathon team.
   - Set `seen_your_work` and `confirmed_by_user`.
3. **Who sits in calibration:** infer it from the process document, quote the sentence, and mark it `inferred`. List the people in the room who haven't seen the user's work.
4. **Precedent:** read recent promotion announcements for what got credited, and write "announcements are narratives, not audits" in the map. Offer the **deep tier** only if the user asks: cross-checking in code, docs and tickets who actually originated the work. It is expensive and off by default.
5. Save.

### Phase 4: Plan
1. **Deadlines:** run `deadlines.py` with the packet deadline. If this cycle's date is published, use it and pass `--published`. Otherwise project last year's date onto this cycle (same month and day, one year later) and leave it `inferred`. Ask the user which holiday or vacation windows are dead time where they are, and pass them as `--dead`. Record "comfortable by X, absolute by Y" with its status and state. If the state is `past`, say so plainly and name the next cycle.
2. **Packet readiness:** for each template section, mark `strong`, `thin` or `empty` from the rubric rows and evidence.
3. **Manager questions:** everything still unknown, plus the readiness question ("is <cycle> realistic, and what's missing?").
4. Run `map_schema.py check`. Fix any errors, then save.
5. Show the user a short summary: the target, the two conversation dates, open rubric gaps, who still needs to see their work, and the questions for their manager. Point to `promotion-map.md`.

## 4. Refresh

1. Run `map_schema.py check`, and read `career/flags.json` if it exists (other skills write staleness signals there, such as a reorg, a departure, or a calendar being published).
2. Re-research only the stale or flagged sections. Keep every other section as it is.
3. Ask the user "anything changed?", covering target, manager, team, and people who have seen their work.
4. If the calendar section is re-checked, or a flag says the calendar was published, re-run `deadlines.py` and update `calendar.manager_conversation`.
5. Update `checked_at` for each re-checked section, clear the flags you handled, and save.

## 5. Packet mode (`/flagrare:promotion packet`)

When the packet deadline approaches, or the user asks:
1. Load the map; if there is none, run the first run first. Gather evidence since the date of the last promotion (or the hire date): use `/flagrare:brag-doc` for windows up to a month and `/flagrare:impact-timeline` for longer ones.
2. Draft the packet in the company's template, from `process.packet_template` (if the template is unknown, use this common shape and say it is a fallback: the header fields, then 2-3 projects (role, estimate vs actual, complexity), mentorship and team building, technical craft, and a list of people to ask for peer quotes).
3. Write each project as action, then measurable result, then impact. Tell a story, not a list of tickets, and name the target-level rubric line each project demonstrates.
4. Save it as `career/packet-draft.md` for the user to edit. **Never submit it anywhere.**
