# Research: Prior art for a whole-document "human editor" prose-review skill

- **Slug:** `2026-07-03-editorial-pass-prior-art`
- **Date:** 2026-07-03
- **Status:** complete
- **Triggered by:** Designing `/flagrare:editorial-pass`, a skill that reviews a document the way a human editor reads it (whole-document cohesion, throughline, pacing) and hunts noise agents leave behind (provenance narration, ruled-out residue, self-referential scaffolding). Goal: survey the published skills ecosystem for prior art on both the review-process structure and the specific deletion categories.
- **Informed:** [`/flagrare:editorial-pass`](../../plugins/flagrare/skills/editorial-pass/SKILL.md) (new skill: two-read protocol, large-to-small order of attention, editorial-memo format, fresh-reader verification).

## Question

What existing Claude skills encode (a) a whole-document, read-like-a-human editorial pass over prose, and (b) removal of operational metadiscourse ("as verified in X") or ruled-out-hypothesis noise, and which of their structures are worth adopting?

## Sources

### [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills)
- **Type:** open-source skill collection (fiction editing)
- **Accessed:** 2026-07-03
- **Relevance:** high
- **What this contributed:** The strongest "human editor" prior art found. Its editorial-review resource defines a two-read protocol and a large-to-small order of attention that `/flagrare:editorial-pass` adopts for nonfiction.
- **Quoted:**
  > "Read the full draft before writing a single note. The first read is for the felt experience [...] Resist the impulse to annotate on first contact. Many apparent problems resolve later in the manuscript; many real problems only become visible in retrospect."

  > "Do not lead with proofreading unless proofreading is the requested edit level. [...] An editorial memo that opens with comma splices when the story has a broken arc is a waste of the author's attention."

  > "Protect the author's voice. The goal is the best version of *this* book by *this* writer, not the book you would have written."

### [anthropics/skills: doc-coauthoring](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md)
- **Type:** official Anthropic skill
- **Accessed:** 2026-07-03
- **Relevance:** high
- **What this contributed:** The whole-document re-read gate near completion ("flow and consistency across sections [...] whether every sentence carries weight") and the fresh-subagent Reader Testing pattern: hand the document alone to a context-free agent and ask what's ambiguous, what knowledge it assumes, and whether it contradicts itself. Adopted as the skill's step-6 verification for high-stakes documents.

### [blader/humanizer](https://github.com/blader/humanizer) and [Aboudjem/humanizer-skill](https://github.com/Aboudjem/humanizer-skill)
- **Type:** open-source skills (AI-tell removal)
- **Accessed:** 2026-07-03
- **Relevance:** medium
- **What this contributed:** The proven per-pattern encoding format (words to watch, problem statement, before/after pair), used for the skill's noise categories. Confirmed the humanizer family targets line-level chat residue ("I hope this helps", knowledge-cutoff disclaimers), not investigation-narration in reports; the two are cousins, not the same category.

### [SNL-UCSB/paper-writing-skill](https://github.com/SNL-UCSB/paper-writing-skill)
- **Type:** open-source skill (academic writing, derived from revision-history analysis)
- **Accessed:** 2026-07-03
- **Relevance:** medium
- **What this contributed:** Two whole-document proxies adopted by the skill (reconstruct the argument from headings alone; every paragraph serves an explicit claim or gets deleted) and the observation that structural rewrites beat incremental polish because "the framing decisions are baked into the sentence structure."

### [obra/the-elements-of-style](https://github.com/obra/the-elements-of-style), [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism), [anthropics skill-authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- **Type:** open-source skills; official authoring guidance
- **Accessed:** 2026-07-03
- **Relevance:** low-medium
- **What this contributed:** Confirmation that the rest of the ecosystem is line-level checklists (Strunk rules, banned-word tables, throat-clearing lists) with no whole-document pass. Authoring guidance shaped the skill's shape: hard rules low-freedom, coherence judgment high-freedom, SKILL.md under 500 lines.

## Findings

1. **The two deletion categories are unnamed in the ecosystem.** No published skill targets provenance narration ("as verified in X", "so-and-so confirmed in the thread") or ruled-out-hypothesis residue ("we confirmed it is not Y") as categories. The nearest fragments are principle-level ("write for the reader, not the requester") or target adjacent problems (chat residue, throat-clearing openers). Naming and encoding them is novel territory.
2. **"Read like a human editor" has real prior art, but only for fiction.** The two-read protocol, large-to-small order of attention, recurring-patterns-not-instances reporting, and query-vs-directive voice protection all come from fiction editing resources and transfer cleanly to technical documents.
3. **A purpose test beats a blanket ban for negative findings.** Incident-postmortem convention values documented dead ends; the skill therefore keeps a ruled-out finding only when a future reader would otherwise redo the investigation, as one line placed where that reader would start digging.
