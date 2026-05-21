---
name: write-docs
description: Procedural guide for writing documentation that lands. Identifies the Diátaxis mode (tutorial / how-to / reference / explanation), picks the shape that fits, applies Google + Microsoft line-level style rules, and treats the README as a special landing-page form modeled on SpacetimeDB / Tokio / RocksDB / Qdrant / Stripe. Use whenever you're writing or restructuring a README, a docs/ tree, a CONTRIBUTING.md, an API reference, or any other documentation surface.
---

# Write docs

Documentation work is not "write good prose." It's identifying which of four distinct genres you're in, picking the shape that fits the genre, then applying line-level style rules that strip out the writerly habits that make docs feel like marketing copy or research notes.

This skill operationalises four sources:

- **[Diátaxis](https://diataxis.fr/)** — the four-mode framework adopted by Python, Ubuntu, Canonical, Cloudflare. Tells you *which kind* of doc you're writing.
- **[Google Developer Documentation Style Guide](https://developers.google.com/style)** — line-level rules: active voice, second person, sentence case, code-font discipline.
- **[Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide)** — the "Top 10 tips" for warm-and-crisp voice: contractions, lead with the verb, fewer words.
- **[Awesome README](https://github.com/matiassingers/awesome-readme)** + real landing pages (SpacetimeDB, Tokio, RocksDB, Qdrant, Stripe) — the shape of a project storefront.

## When to invoke

- The user asks you to write or restructure a README, a `docs/` tree, a CONTRIBUTING.md, an API reference, a getting-started guide, an architecture document, a runbook, a release note, or any other documentation surface.
- After implementing a feature whose docs need to land alongside the code in the same commit.
- During a staleness audit when documentation drift is the blocker.
- Whenever the user invokes `/write-docs` explicitly.

This is **not** the skill for changelogs or release notes specifically — those are `/release-check`'s job, which has its own Valve Dota patch-notes style guide.

## Procedure

### 1. Identify the Diátaxis mode

Every documentation page belongs to exactly one of four modes. Identify which before writing a single line.

| Mode | Question it answers | Audience state | Form |
|---|---|---|---|
| **Tutorial** | "How do I learn this?" | Novice; seeking confidence | Narrative, imperative, step-by-step, conversational |
| **How-to guide** | "How do I do X?" | Competent; pursuing a specific goal | Directive, conditional, assumption-laden, functional |
| **Reference** | "What is/are…?" | Practitioner; seeking facts | Declarative, structured, comprehensive, impersonal |
| **Explanation** | "Why? What does this mean?" | Learner; seeking context | Discursive, exploratory, background-oriented, objective |

#### Decisive tests when the call is close

- **Tutorial vs. how-to**: Is the user *learning the domain*, or *already trying to do something specific*? A tutorial assumes no prior task context.
- **How-to vs. reference**: Does the content assume the user knows *why* they're here? How-to assumes a goal. Reference is goal-agnostic.
- **Reference vs. explanation**: Is this *what it is*, or *why it matters*? Reference catalogs. Explanation contextualises.
- **Explanation vs. tutorial**: Is this building *understanding* or *capability*? Explanations don't guide action.

If you can't pick one mode, the page is trying to do two jobs. Split it.

### 2. Choose the shape that fits the mode

Once the mode is fixed, the shape is mostly fixed too. Don't invent a new structure — reach for the conventional one.

#### Tutorial shape (~300–800 lines per page)

1. **What you'll build** — one sentence + a finished-state screenshot or output.
2. **Prerequisites** — a checklist, not prose.
3. **Steps** — numbered, imperative, complete-and-checkable. Every step ends with the user seeing something change.
4. **What you learned** — three or four bullets naming concepts the user just touched.
5. **Where to go next** — links to relevant how-to guides or reference.

Tutorial rule: **the project must finish.** A tutorial without a finished artifact is a tour. Tours are anti-pattern.

#### How-to shape (~50–200 lines per page)

1. **Goal** — one sentence stating what the reader is trying to accomplish.
2. **Prerequisites** — what state the reader must be in.
3. **Procedure** — numbered, conditional where needed ("if you're using X, do A; otherwise do B"). No background; no theory.
4. **Result** — one sentence describing what should now be true.

How-to rule: **assume the reader has a goal.** No explainers, no concept dumps. If a step needs a concept, link to the explanation page.

#### Reference shape (no length cap — atomic entries)

1. **Synopsis** — the signature, one line.
2. **Description** — one paragraph max.
3. **Parameters** — table or definition list, one row each.
4. **Returns / Exceptions / Side effects** — exhaustive.
5. **Example** — one minimal call.

Reference rule: **every entry stands alone.** Scannable, atomic, consistent structure across siblings. Reference doesn't lecture.

#### Explanation shape (~100–400 lines per page)

1. **The question** — frame the problem the page exists to answer.
2. **Background** — context the reader needs to follow the argument.
3. **The shape of the answer** — discursive but bounded.
4. **Trade-offs** — what we chose differently and why.
5. **See also** — pointers to reference and how-to material.

Explanation rule: **don't prescribe action.** Use "we", explore alternatives, name the tension. Then stop.

### 3. Apply universal line-level style

These rules apply across all four modes. They're the Google + Microsoft synthesis.

**Voice and person:**

- **Active voice by default.** "The server sends acknowledgment" ✓, "Acknowledgment is sent by the server" ✗. Passive only when (a) the object is what matters, (b) the actor is irrelevant, (c) blame-avoidance.
- **Second person addressing the reader.** "You can create a website" ✓, "We can create a website" ✗.
- **"We"** refers to the project / authoring organisation only, and only when the antecedent is unambiguous.
- **Imperative for instructions.** "Click Submit" ✓, "You should click Submit" ✗.
- **Present tense.** "The request returns 200" ✓, "The request will return 200" ✗.

**Tense and length:**

- **Lead with the verb.** "Save time by creating a template" ✓ beats "Templates provide a starting point" ✗. Microsoft's "revise weak writing" rule: edit out "you can" and "there is / there are."
- **Fewer words.** Microsoft headline rule. *"If you're ready to purchase, contact your representative"* → *"Ready to buy? Contact us."*
- **Contractions are fine.** "You're", "it's", "we're". They're warm without being unprofessional.
- **Get to the point fast.** Front-load keywords. Don't bury the action under preamble.

**Headings:**

- **Sentence case.** "Create an instance" ✓, "Create An Instance" ✗. Microsoft: *Never Use Title Capitalization (Like This). Never Ever.*
- **Bare infinitive for tasks**, noun phrase for concepts. "Create an instance" ✓ for a how-to; "ML model monitoring overview" ✓ for an explanation. Never start a heading with an `-ing` gerund.
- **No end punctuation on headings**, UI titles, or three-or-fewer-word list items.
- **Parallel structure across siblings**. If H2 #1 starts with a verb, H2 #2 starts with a verb.

**Code formatting:**

- **Code font (backticks) for verbatim text:** filenames, paths, attributes, methods, env vars, HTTP status codes.
- **Plain text for concepts and product names:** "Google Docs", "the database", "your project". `Google Docs` ✗.
- **Placeholders are UPPERCASE in code font.** Replace `SUBNETWORK_NAME` with your subnet. Not `<subnetwork_name>`, not `{subnetwork_name}`.
- **Never inflect a code token as English.** "Send a `POST` request" ✓, "`POST` the data" ✗.

**Lists and punctuation:**

- **Oxford comma always.** "Android, iOS, and Windows" ✓, "Android, iOS and Windows" ✗.
- **One space after a period.** Not two.
- **Em-dashes have no surrounding spaces.** "Use pipelines—logical groups—to consolidate" ✓.

### 4. The README is a special form

A README is not a docs page. It's the project's storefront — the only thing many readers will ever see. It serves all four Diátaxis modes at once in compressed form, plus does brand work the other docs don't have to.

The shape that wins (verified across SpacetimeDB, Tokio, RocksDB, Qdrant, Stripe homepage, dvc, choo, gofiber):

```
1. Title + ≤6 badges (one row, no vanity badges)              ~5 lines
2. Status line + 2-3 sentence pitch                           ~10 lines
3. Hero example — runnable, real, copy-pasteable              ~20 lines
4. Why / decision criterion ("use this when / reach for X     ~15 lines
   else when")
5. Features table (Capability → Status → Where to learn more) ~20 lines
6. Performance snapshot (3-5 honest numbers, link to bench)   ~20 lines
7. Architecture diagram + one paragraph                       ~25 lines
8. Quick start (one path per audience, audience-tagged)       ~30 lines
9. Project status (current version, what's stable, what's     ~15 lines
   experimental, one-sentence audit link if relevant)
10. Documentation map (Architecture, Guides, Community,       ~15 lines
    Roadmap)
11. FAQ (name origin, "isn't this just a KV cache?", design   ~30 lines
    principles, terse comparison table) — short, scannable
12. Acknowledgments + License + Citation                      ~10 lines

Target total: 200-300 lines.
```

#### Above-the-fold rule

The first 80 lines must answer: *what is this, why should I care, how do I try it.* That's title + badges + status + pitch + hero. No retraction walls, no research diary entries, no 30-item milestone checklists.

#### What stays out

- Long narrative introductions ("Once upon a time…").
- Generic motivational language ("revolutionise", "game-changer").
- A Table of Contents in a ≤500-line doc.
- The full changelog (link to `CHANGELOG.md`).
- The full roadmap (link to `docs/roadmap.md`).
- Detailed installation steps (link to the contributor / user guide).
- Multiple "Getting Started" sections for different audiences without explicit audience tagging.

#### What's hidden but mandatory

- The README must link to: `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff` (if research-adjacent).
- It must have a Status line that's truthful. "Research-grade preview", "Beta", "Stable", "Archived" — pick one.
- It must have a runnable hero example. If you can't write a 10-line snippet that works on `pip install <name> && python -`, your project's onboarding is broken before docs are.

### 5. Self-check before publishing

Run through:

1. **Mode fit.** For every page: which Diátaxis mode is this? Could I explain it in one sentence? If not, split.
2. **Anti-pattern scan.** Did I write a tutorial that's actually a tour? A reference that lectures? An explanation that prescribes? Re-read with these in mind.
3. **First 80 lines (for READMEs).** Does the reader know what the project is, who it's for, and how to try it?
4. **Voice scan.** Open three random sections. Are they in active voice, second person, present tense, sentence case? If any of those is "no", fix.
5. **Code-font scan.** Are filenames / methods / env vars in backticks? Are product names *not* in backticks?
6. **Link integrity.** Every internal link resolves. Every external link points at a stable URL (not a random tweet).
7. **Length sanity.** If a README is over 400 lines, you're scaling the storefront with the codebase. Cut.

## Output

For substantive doc work, return:

```
Pages written: <N>
Mode breakdown: <X tutorials, Y how-tos, Z reference, W explanations>
Cross-links: <internal links added>
Style adjustments: <count of voice / case / code-font fixes>
Anti-patterns removed: <list, brief>
README line count: <if applicable, with target range>
```

For a single doc, just say what was written and which Diátaxis mode it occupies.

## Anti-patterns

These show up over and over in documentation reviews. Catch them at write time.

- **Tutorial that's a tour.** "Look at this feature, look at that feature" with no project the user finishes building. A tutorial without a finished artifact is a brochure.
- **Reference that lectures.** "This is important because…" inside an API reference entry. Reference catalogs; explanation contextualises. Move the rationale to an explanation page and link it.
- **How-to that's actually concept dump.** If your "how to deploy" page spends three paragraphs explaining what deployment is, you have an explanation page wearing a how-to costume.
- **Explanation that prescribes.** "Here's why X matters — therefore do Y." Explanation is discursive. If the page ends with a procedure, it's two pages glued together.
- **README narrative intro.** "Once upon a time, the team was frustrated with…" — gone. Title, badges, pitch, hero. The reader's tolerance for prose increases monotonically with screen depth.
- **README marketing copy.** "Revolutionary", "game-changing", "next-generation". If the project is good, the hero example shows it. If it isn't, no adjective fixes it.
- **README that doesn't have a hero example.** The single most important section. Without it, the project is selling concepts, not capability.
- **Tooling-generated CHANGELOG entries shipped verbatim.** Tooling output is a starting point, not a final product. See `/release-check` for the rewrite discipline.
- **Multiple "Getting Started" sections without audience labels.** Rust contributor vs Python user vs evaluator are three different journeys. Either give each one a tagged subsection or pick the canonical one and link out for the others.
- **Title case headings.** "Create An Instance" is dead. "Create an instance" is what every major modern style guide uses.
- **`-ing` heading openings.** "Transferring data sets" → "Transfer data sets". Gerunds increase character count and translate inconsistently.
- **Code font on product names.** `Google Docs` reads as a class name. Google Docs reads as a product.

## Cross-references

- `/atdd-plan` for the doc structure that ships *alongside* a feature.
- `/staleness-audit` runs before commit and surfaces doc drift (broken cross-links, stale version claims, removed-symbol references).
- `/release-check` handles changelog / release-note writing, which has its own style guide (Valve Dota patch notes) — do not duplicate that work here.
- `/research-catalog` cross-links research artifacts back to the consuming docs.

## Why this exists

The field of "documentation writing" is bigger than any single skill can hold. What it lacks is a *named* short-form discipline — most online guidance is either platitudes ("write clearly!") or vendor-specific schemas (Mintlify, GitBook). The actual gold-standard sources — Diátaxis, Google, Microsoft, Stripe, Awesome README — are stable, opinionated, and citeable, but no widely-circulated Claude skill currently bundles them.

This skill is the bundle: Diátaxis for *which kind of doc*, Google + Microsoft for *how to write the sentences*, the celebrated-READMEs pattern for *the storefront*. Each section names its source so you can verify the rule directly when something feels wrong.

The most expensive documentation failure is not a single bad page — it's a project whose docs grow without a shape, where every page has its own register, where the README is 756 lines because it absorbs every new feature's narrative, where a "tutorial" turns out to be a tour and a "reference" turns out to be a lecture. Those failures are recoverable but expensive (the project tracked in `/home/flagrare/Dev/ares-project/tardigrade-db` cut its README from 756 lines to 229 in May 2026 — that was a four-hour restructure). Catching the wrong mode at write time costs nothing.
