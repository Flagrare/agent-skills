# Research: Existing ASD-STE100 (Simplified Technical English) agent skills

- **Slug:** `2026-11-24-ste100-skills-prior-art`
- **Date:** 2026-11-24
- **Status:** complete
- **Triggered by:** A request to find existing ASD-STE100 skills that the writing skills (write-docs, humanizer, editorial-pass) could reuse or learn from
- **Informed:** [`/flagrare:controlled-english`](../../plugins/flagrare/skills/controlled-english/SKILL.md)

## Question

Which published agent skills apply ASD-STE100 Simplified Technical English to LLM output, how good are they, what can we legally reuse, and do they beat a short style prompt?

## Sources

### [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)
- **Authors / Org:** danyuchn (single author)
- **Type:** open-source project (MIT)
- **Published:** ongoing, last push 2026-11-24, about 6.9k stars
- **Accessed:** 2026-11-24
- **Relevance:** high
- **What this contributed:** The clearest design: two modes (Strict for error messages, tool descriptions and agent instructions; STE-flavored for READMEs, PR descriptions and changelogs). It splits rules into structural ones you can check without the ASD dictionary and lexical ones you cannot, and tells the model not to claim dictionary compliance. Ships `scripts/ste-lint.py`, a rules reference and before/after examples.
- **Quoted:**
  > "Apply the structural rules with confidence. Apply the lexical rules as a direction of travel"

### [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)
- **Authors / Org:** AminBlg (single author)
- **Type:** open-source project (MIT)
- **Published:** ongoing, last push 2026-11-10, about 4.7k stars
- **Accessed:** 2026-11-24
- **Relevance:** high
- **What this contributed:** The only candidate with a real eval suite: 9 Claude models x 8 tasks, a regex linter and a blind pairwise judge. It reports 81.3% fewer violations per 100 words and 62 of 72 judge wins. Its own `evals/results/WHY-USELESS-2026-09-02.md` is the key dissent: on chat replies, an 8-line prompt beat the full skill on length, em dashes, bold and headers, and the skill won only on its own linter.
- **Quoted:**
  > "Skill wins only on its own linter. Micro wins on everything a reader sees."

### [nuelcyoung/asd-ste100](https://github.com/nuelcyoung/asd-ste100)
- **Authors / Org:** nuelcyoung
- **Type:** open-source project (MIT), 46 stars, last push 2026-11-18
- **Accessed:** 2026-11-24
- **Relevance:** low
- **What this contributed:** Confirms Issue 9 (2025) is the current standard. Covers the same write, rewrite and check modes with no evals.

### [jjsnack/technical-language-skill](https://github.com/jjsnack/technical-language-skill) and [zorost/oneread](https://github.com/zorost/oneread)
- **Authors / Org:** jjsnack (GPL-3.0, 0 stars); zorost (MIT, 1 star)
- **Type:** open-source projects
- **Accessed:** 2026-11-24
- **Relevance:** low
- **What this contributed:** jjsnack ships a linter plus an advisory hook, but GPL-3.0 rules out copying into an MIT repo. oneread is a linter, GitHub Action and MCP server for STE100 checks, too new to rely on.

## Synthesis

Two skills are worth reading: danyuchn's for its design, AminBlg's for its evals. Both are MIT, so ideas and code can be borrowed with credit.

None of them can ship the ASD dictionary, which is copyrighted. So every skill really enforces the structural rules only: active voice, no phrasal verbs, one instruction per sentence, length caps of 20 to 25 words, no semicolons, noun clusters of at most 3 words.

AminBlg's own negative result matters most for us. A 50+ rule skill dilutes the few rules that matter, and models game the gaps (for example, bulleting everything when list items are exempt from the cap). A short prompt with 5 rules did better on replies. For prose aimed at people, adding a full STE skill on top of an existing short style rule set is likely a loss.

Where STE does fit is text an agent or tool parses: tool descriptions, error messages, agent instructions. danyuchn's Strict mode targets exactly that.

## Downstream uses

- Chat answer comparing the candidates (2026-11-24)
- [`/flagrare:controlled-english`](../../plugins/flagrare/skills/controlled-english/SKILL.md): modes, structural rules, the user's own dictionary as a setting, and the advice to skip chat replies
