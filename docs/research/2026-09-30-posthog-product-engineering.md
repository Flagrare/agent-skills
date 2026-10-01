# Research: how product engineering works at PostHog

- **Slug:** `2026-09-30-posthog-product-engineering`
- **Date:** 2026-09-30
- **Status:** complete
- **Triggered by:** Designing `/flagrare:opportunity-scan`: how engineers who own problems end to end find and frame their work, and how that sits next to product managers.
- **Informed:** the [career skills design](../plans/2026-09-30-career-skills-design.md): opportunity-scan's proposal shape (problem, hypothesis and success metric set before building, smallest first step) and its rule that a proposal feeds the product decision instead of going around it. Related: [what gets engineers promoted](./2026-09-30-what-gets-engineers-promoted.md).

## Question

How does PostHog run product engineering: what a product engineer owns, how work gets chosen and prioritized, how much autonomy engineers have and where it stops, and what product managers and managers do if they don't assign tasks?

## Method note

Three research agents read PostHog's handbook, blog and newsletter through a summarising fetch tool. Every quote used in the synthesis was then checked against the raw page text (`posthog.com/page-data/<path>/page-data.json`). Quotes marked "(verified)" matched the raw text. Paraphrases and search-snippet claims are labeled as such.

## Sources

### [Managers and management](https://posthog.com/handbook/company/management)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc (company handbook)
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** The direct answer to "do managers assign tasks": they are told not to. It lists what managers do (set context, 1-1s, hiring help, onboarding, keeper test) and what they don't (set tasks, hire/fire, set pay).
- **Quoted (verified):**
  > "Setting tasks for your direct reports - that is not how small teams work"
  > "At PostHog, we hire highly experienced people for 99% of roles. That means managers won't need to spend time telling their direct reports what to do."
  > "Management is intentionally spread thin at PostHog. This is a forcing function for making sure that teams and ICs continue to have high levels of autonomy."
  > "Deciding to hire or fire people - the exec team do this"

### [Small teams](https://posthog.com/handbook/company/small-teams)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** The unit of work: 2-6 people, one team per engineer, a team lead who decides what to build, and reporting lines that run by function (engineers report to engineers).
- **Quoted (verified):**
  > "A small team should *strictly* be between 2-6 people."
  > "The team lead has the final say in a given small team's decision-making - they decide what to build / work on."
  > "managers don't set tasks" (from "it's critical that managers don't set tasks for those in small teams")
  > "Product engineers should never be in more than one team."

### [What product managers do at PostHog](https://posthog.com/handbook/product/product-manager-role)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** PMs exist but own context, not the roadmap. They join only once a product has revenue, and the direction of "assigning" is reversed: the team can assign work to the PM.
- **Quoted (verified):**
  > "They do not own roadmaps or dictate what to build next."
  > "Engineers choose what to work on next based on shared context."
  > "A PM typically chooses their own projects, but the team and team lead can "assign" them tasks when needed."
  > "stage 3" (a PM is added after a product launches and generates revenue)

### [Product teams](https://posthog.com/product-engineer/product-teams) and [Creating a product engineering culture](https://posthog.com/product-engineer/culture)
- **Authors / Org:** PostHog (uncredited)
- **Type:** vendor doc / engineering blog
- **Published:** unknown
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** The strongest autonomy statements, and PostHog's own caveat that the model isn't for everyone.
- **Quoted (verified):**
  > "complete autonomy" / "Engineers own product decisions" / engineers are "responsible and accountable" for acting on PM context
  > "product managers at PostHog don't manage product teams, or engineers"
  > "resist your urge to control"
  > "Not everyone needs to be a product engineer"

### [Setting quarterly goals](https://posthog.com/handbook/company/goal-setting)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** Where the top-down part lives: execs set company direction each quarter, then each small team sets its own objectives with one named owner, and outcomes beat output.
- **Quoted (verified):**
  > "We plan objectives every quarter."
  > "small teams set their own objectives"
  > "one named owner"
  > "more important than shipping specific things"

### [Shipping and releasing (development process)](https://posthog.com/handbook/engineering/development-process)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** medium
- **What this contributed:** The execution cadence: two-week sprints planned by the team itself, PR review before merge, and no release gates like merge freezes.
- **Quoted (verified):** "probably achievable" (sprint work should be concrete and probably achievable in 2 weeks); "Friday afternoon" (merge anytime, including Friday afternoon).

### [Culture](https://posthog.com/handbook/company/culture) and [We're a wide company with small teams](https://posthog.com/handbook/wide-company)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** medium
- **What this contributed:** Bias to action and the limit of autonomy: engineers don't ask permission, but the exec team decides which products exist.
- **Quoted (verified):**
  > "Default to *not* asking for permission to do something if you are acting in the best interests of PostHog. It is ok to ask for more context though."
  > "just create the pull request"
  > "Decide which products to build" (exec team remit)

### [Product management is broken. Engineers can fix it](https://posthog.com/newsletter/product-management-is-broken)
- **Authors / Org:** James Hawkins (CEO) and Lior Neu-ner, PostHog
- **Type:** engineering blog (newsletter)
- **Published:** 2024-12-03
- **Accessed:** 2026-09-30
- **Relevance:** high
- **What this contributed:** The CEO's own account: he once thought PostHog needed no PMs and changed his mind, and he describes the quarterly loop (execs share goals, engineers propose, the CEO assumes the team is right). It also names the precondition.
- **Quoted (verified):** "partially" (from "I was (partially) wrong"); "need product managers"; "what the team has come up with is correct"; "extremely high-level of trust".

### [How we decide what to build](https://posthog.com/newsletter/how-we-decide-what-to-build)
- **Authors / Org:** PostHog newsletter
- **Type:** engineering blog
- **Published:** unknown
- **Accessed:** 2026-09-30
- **Relevance:** medium
- **What this contributed:** The mechanics of choosing features (the team brainstorms, votes, and names a single owner who carries the feature end to end), plus the date PMs arrived.
- **Quoted (verified):** "October 2022" (first PMs); "voted"; "The owner becomes responsible for validating the idea, implementing the feature, making tweaks and bug fixes, and ensuring ongoing success."

### [Support hero](https://posthog.com/handbook/engineering/operations/support-hero)
- **Authors / Org:** PostHog handbook (uncredited)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-09-30
- **Relevance:** medium
- **What this contributed:** One of the input channels for work: engineers rotate weekly through their team's customer support.
- **Quoted (verified):** "Support Hero" (the role exists; the weekly per-team rotation is paraphrased from the fetch summary).

### Secondary and unverified (used only as color)
- [What is a product engineer](https://posthog.com/product-engineer/what-is-a-product-engineer), [Traits of product engineers](https://posthog.com/product-engineer/traits), [Product engineer vs product manager](https://posthog.com/blog/product-engineer-vs-product-manager) (Ian Vanagas, 2023-01-24), [Why product engineer is the most fun role](https://posthog.com/blog/why-product-engineering-is-so-fun) (Raquel M Smith, 2023-02-02), [Compensation](https://posthog.com/handbook/people/compensation), [Product Engineer job post](https://posthog.com/careers/product-engineer): role definition, traits, levels and pay. Read through the summarising tool only, quotes not raw-checked.
- [Reader comments on the Hawkins post](https://newsletter.posthog.com/p/product-management-is-broken-engineers/comments): the only dissent found. Commenters argue engineers shouldn't own roadmaps and that the model may only work for a developer-tools company with unusually strong engineers. These are comments, not analysis. No Pragmatic Engineer or Lenny's Newsletter critique was found.

## Synthesis

**Your guess is right: nobody hands PostHog engineers tickets.** Managers are told in writing that setting tasks for reports is "not how small teams work" ([management](https://posthog.com/handbook/company/management)). PMs "do not own roadmaps or dictate what to build next" ([PM role](https://posthog.com/handbook/product/product-manager-role)). The only "assigning" in the handbook runs the other way: the team can "assign" work to the PM.

**How work actually reaches an engineer.** The loop is top-down on goals and bottom-up on what gets built:
1. Each quarter the exec team sets company direction and decides which products exist ([goal-setting](https://posthog.com/handbook/company/goal-setting), [wide company](https://posthog.com/handbook/wide-company)).
2. Each small team (2-6 people) sets its own objectives, each with one named owner. The team lead has the final say on what the team builds ([small teams](https://posthog.com/handbook/company/small-teams)).
3. Inside that, engineers pick work from what they see: user conversations, support rotation, usage data, the public roadmap. Teams brainstorm, vote, and give each feature a single owner who validates, builds, fixes and measures it ([how we decide](https://posthog.com/newsletter/how-we-decide-what-to-build)).
4. The team plans its own two-week sprints, reviews its own PRs, and ships without an outside QA or release gate ([development process](https://posthog.com/handbook/engineering/development-process)).

**What managers and PMs do instead.** Managers mostly keep doing their craft (engineers code) and "set context": a roadmap to work toward, customer understanding, 1-1s, hiring help, and the keeper test. Hiring, firing and pay sit with the exec team, not managers. PMs arrive only once a product has revenue. They supply data, discovery systems, metrics, pricing and growth reviews, and engineers are accountable for acting on that context ([product teams](https://posthog.com/product-engineer/product-teams)).

**Where autonomy stops.** Engineers don't pick which products the company builds, don't restructure teams, and don't set pay. Accountability is sharp rather than procedural: named owners per objective, the keeper test, and pay reviews that weigh "consistently hitting ambitious objectives".

**The honest caveats.** The CEO says it "requires an extremely high-level of trust" in engineers, and that he was "(partially) wrong" about never needing PMs ([Hawkins, 2024](https://posthog.com/newsletter/product-management-is-broken)). PostHog says "Not everyone needs to be a product engineer." Outside critics argue it works because PostHog builds for engineers and hires unusually senior people ("99% of roles" are highly experienced, per the management page). It is a deliberate bet at a specific company, not a free-standing best practice.

## Downstream uses

- [career skills design](../plans/2026-09-30-career-skills-design.md), the `opportunity-scan` section.
- `/flagrare:opportunity-scan` SKILL.md: the proposal template and the decision-process rule.
