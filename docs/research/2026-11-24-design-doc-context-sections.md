# Research: How good design docs write their context section

- **Slug:** `2026-11-24-design-doc-context-sections`
- **Date:** 2026-11-24
- **Status:** complete
- **Triggered by:** A TDD's context section named a metric and a gap, but never gave a real case, a reason for "why now", or who gains. The user asked what good references do differently.
- **Informed:** [`/flagrare:tdd-writer`](../../plugins/flagrare/skills/tdd-writer/SKILL.md): the Context template, "Writing the context", Key decisions, and the review checks.

## Question

What moves do well-regarded design docs make in their context or motivation section, and in what order?

## Sources

### [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- **Authors / Org:** Malte Ubl
- **Type:** engineering blog
- **Published:** 2020-07-06
- **Accessed:** 2026-11-24
- **Relevance:** high
- **What this contributed:** Context holds objective background facts only. Goals and non-goals are separate, and a non-goal is something that could reasonably have been a goal. Keep the section succinct.
- **Quoted:**
  > "Keep it succinct!"

### [Rust RFC template](https://github.com/rust-lang/rfcs/blob/master/0000-template.md) and [RFC 3058, try_trait_v2](https://github.com/rust-lang/rfcs/blob/master/text/3058-try-trait-v2.md)
- **Authors / Org:** Rust project; RFC 3058 from [rust-lang/rfcs#3058](https://github.com/rust-lang/rfcs/pull/3058)
- **Type:** open-source project process + spec
- **Published:** ongoing; RFC 3058 started 2020-12-12
- **Accessed:** 2026-11-24
- **Relevance:** medium
- **What this contributed:** Motivation names the user's problem with specific use cases, before any solution. RFC 3058 opens from the prior decision, then lists what new information broke it, then proposes. That is the "what changed since" move.

### [Kubernetes KEP template](https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md)
- **Authors / Org:** Kubernetes SIG Architecture
- **Type:** open-source project template
- **Published:** ongoing
- **Accessed:** 2026-11-24
- **Relevance:** medium
- **What this contributed:** Motivation states benefits to users. Goals answer "how will we know this succeeded?". Non-goals focus the discussion. User stories make it feel real without implementation detail.
- **Quoted:**
  > "make this feel real for users without getting bogged down"

### [PEP 1](https://peps.python.org/pep-0001/) and [PEP 572, Assignment Expressions](https://peps.python.org/pep-0572/)
- **Authors / Org:** PEP 1 by Barry Warsaw, Jeremy Hylton, David Goodger, Alyssa Coghlan; PEP 572 by Chris Angelico, Tim Peters, Guido van Rossum
- **Type:** spec / process
- **Published:** PEP 1 created 2000-06-13, active; PEP 572 created 2018-02-28
- **Accessed:** 2026-11-24
- **Relevance:** medium
- **What this contributed:** A short abstract up front, then why the status quo is inadequate. PEP 572 argues that examples must come from real code, not toy cases, and it names the formal and informal terms up front.
- **Quoted:**
  > "examples should be rooted in real code"

Not read: the Pragmatic Engineer RFC article (404) and Angela Zhang's Medium guide (403). Oxide's RFD 1 was read but dropped, because it covers process, not context.

## Synthesis

These sources draw on overlapping moves. No single source has all of them, but together they suggest this order:

1. **What exists today.** The reader's starting point in plain words, with the key terms defined ([Google](#design-docs-at-google)).
2. **The problem, made concrete.** A real user or a real case, not an abstraction ([Rust](#rust-rfc-template-and-rfc-3058-try_trait_v2), [KEP](#kubernetes-kep-template), [PEP 572](#pep-1-and-pep-572-assignment-expressions)).
3. **Why now.** What changed since the last decision. Only [RFC 3058](#rust-rfc-template-and-rfc-3058-try_trait_v2) does this explicitly: "new information has come in since the previous RFC".
4. **Impact and who it matters to.** How success is measured ([KEP](#kubernetes-kep-template)).
5. **Goals and non-goals.** A non-goal is something a reviewer would reasonably expect ([Google](#design-docs-at-google)).
6. **Links for depth.** Link earlier work instead of re-explaining it ([Google](#design-docs-at-google), [RFC 3058](#rust-rfc-template-and-rfc-3058-try_trait_v2)).

Context holds background facts. Mechanics, field names and production counts belong in the design itself ([Google](#design-docs-at-google)). Google and RFC 3058 keep examples out of context and show them in the design, while the Rust template, KEPs and PEP 572 want real cases early. The before/after screenshots come from company TDD guidance, not from these public sources.

## Downstream uses

- [`/flagrare:tdd-writer`](../../plugins/flagrare/skills/tdd-writer/SKILL.md), v1.84.0
