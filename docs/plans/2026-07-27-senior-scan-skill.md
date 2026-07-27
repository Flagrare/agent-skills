# Senior scan skill

> No em-dashes in this document (repo hook enforces it in generated `.md`).

Named `senior-scan` after its purpose: scanning the org's communication surfaces for
openings to operate at the next level. Promotions lag behavior, so the skill treats
"weighed in where it mattered" as the leading activity and keeps the evidence trail as
the lagging indicator.

## Problem

An engineer working toward promotion needs influence beyond their assigned tickets:
shaping decisions, unblocking people, answering the questions only they can answer.
Those openings are scattered across Slack threads and open PRs, decay fast (a decision
made without you is gone), and are invisible unless you happen to read the right thread
at the right time. Reading everything doesn't scale, and commenting everywhere is worse
than commenting nowhere: shallow drive-bys read as noise and hurt the case they were
meant to build.

## Shape

1. **One parallel read-only sweep agent per configured surface** hunts four signals:
   decisions still forming, people stuck or circling, discussions missing context the
   user has, and cross-team changes touching the user's systems. Surfaces come in
   three kinds (chat, code review, docs/tickets) and are chosen at onboarding from
   the MCPs actually connected, following standup-report's `extra_mcps` detect-and-opt-in
   pattern. Slack and GitHub are reference implementations with detailed sweep
   instructions; every other surface runs a generic sweep driven by the same four
   signals, with docs surfaces treating open RFC comment periods as prime candidates
   (a decision with an explicit window).
2. **A five-axis score** (leverage, credibility, stretch, audience, timing) ranks
   candidates, with a hard filter: Leverage 0 or Credibility 0 kills the item
   regardless of visibility. That rule is the skill's identity; it exists to make
   performative commenting impossible.
3. **A digest with drafts.** Max 5 items, fully contextualized (the user hasn't read
   the threads), each with a draft reply in the user's voice. Nothing ever posts
   without per-message approval. A "skipped but notable" section keeps the filter
   honest and tunable.
4. **An evidence trail.** Posted contributions append to `contributions.log.md` with
   the target behavior they exercised; `/flagrare:brag-doc` treats it as a source.

## Conventions reused

- Shared config at `~/.claude/skills/flagrare/config.json` (top-level identity keys,
  skill block under `skills["senior-scan"]`), per the standup-report / brag-doc pattern.
- Mutable state at `~/.claude/skills/flagrare/senior-scan/` (survives plugin updates),
  per the daily-code-review teams pattern.
- Onboarding is discovery-first: propose channels, repos, and domains from the user's
  real activity and have them confirm, rather than asking them to compose lists from
  memory. Voice rules are distilled from the user's own recent messages when reachable.

## Eval prompts

Kept from the original design session, for future skill-creator iterations:

1. "run a senior scan"
2. "I've been heads down for two days. anything on slack or in open PRs I should weigh in on?"
3. "catch me up. where can I have the most impact today?"

The last two test triggering without the skill being named. Expected across all three:
digest respects the hard filter, drafts follow voice rules, state written, nothing posted.
