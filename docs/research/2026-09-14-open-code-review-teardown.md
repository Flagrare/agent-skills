# Open Code Review: Teardown and What Our Review Skills Should Absorb

**Research date:** 2026-09-14
**Source:** [alibaba/open-code-review](https://github.com/alibaba/open-code-review), Apache-2.0, read locally at `~/Dev/labs/open-code-review`
**Purpose:** OCR is a production AI code review CLI whose prompts solve several problems our review skills currently leave to the model's judgement. This catalogues what is genuinely absorbable, what is a deliberate design disagreement, and what we already do better, so nobody overcorrects.

**Attribution note:** every prompt cited below lives under `internal/config/template/prompts/` in the OCR repo and is Apache-2.0. Quotes here are paraphrased and sanitized (OCR's prompts use em-dashes freely; ours cannot). If any of this text is later absorbed into a skill, the attribution is already recorded here.

---

## 1. What OCR is, structurally

A Go CLI that reads git diffs and emits line-anchored review comments. The pipeline is worth knowing because the shape is the lesson:

```
changed files
   -> GROUPING TASK      cluster files into semantically related review groups
   -> (per group, N rounds where N = effort level)
        -> PLAN TASK     risk analysis, threshold-gated, produces severity-tagged
                         issues plus which context tools to reach for
        -> MAIN TASK     the actual review, tool-using, emits comments
   -> REVIEW FILTER      a separate diff-blind fact-check pass that can only remove
   -> RE-LOCATION TASK   re-anchor a comment whose snippet failed to match
```

Five distinct prompts with five distinct jobs. Our skills collapse the middle three into one subagent brief per concern. That collapse is not wrong, but it hides some decisions OCR had to make explicit, and those decisions are the value here.

The repo also ships two Claude Code skills of its own (`skills/open-code-review/`, `skills/open-code-review-delegate/`). The delegate skill is the more interesting of the two: it uses the CLI only for deterministic work (file selection, rule resolution) and hands the actual reviewing to the host agent. That is structurally the same position our skills are in, so its instructions transfer almost directly.

---

## 2. Absorbable, ranked by value per unit of cost

### 2.1 Coverage accounting (cheapest, highest value)

**What they do.** The delegate skill makes file coverage a hard output requirement:

> Create a checklist containing every reviewable file. Use (path, status) as the checklist identity. Mark each file reviewed, or skipped with a concrete reason. Include total_files, reviewed_files, skipped_files and coverage_rate in the summary. Every entry must end as reviewed or explicitly skipped; do not silently omit files.

And the main review prompt closes the most common loophole by name:

> Reviewing an implementation file does not cover its header, interface, or configuration counterpart. A file being the smaller or secondary member of the group is not a reason to skip it.

**What we have.** Nothing. `pr-reviewer` hands each of five subagents "the full PR diff" and trusts them to get through it. `implementation-review` does the same with the staged diff. A subagent that read 14 of 20 files and reported three findings is indistinguishable in its output from one that read all 20 and reported three findings. On a large PR the first case is the likely one, and it is invisible.

**What to change.** Require every review subagent to return a coverage line before its findings: files seen, files reviewed, files skipped with a one-phrase reason each. Then have the synthesising step in Step 7 (pr-reviewer) and Step 3 (implementation-review) refuse to print a verdict when coverage is partial and unexplained. This is a few sentences per brief and it converts a silent failure into a visible one.

The secondary-file rule is worth lifting verbatim in spirit: the config file, the interface, the barrel export and the type declaration are exactly what a reviewer skips, and exactly where contract drift lives.

### 2.2 Tool-call budget and the stop-probing guard

**What they do.** OCR's scan-mode prompt (`internal/config/template/scan_template.json`) spends a whole section on this:

> Your tool-call budget per file is limited. Limit context-gathering to at most 2 or 3 tool calls per finding. Avoid calling the same tool with the same arguments more than once. Once you have enough evidence for an issue, record the comment immediately rather than gathering more context. If no further issues are evident after a quick sweep of the file, finish immediately; do not keep probing for marginal findings.

**What we have.** No budget, and no permission to stop. Our subagent briefs are written as checklists ("scan for these patterns", a table of eight scenario types), which reads to a subagent as an obligation to produce a finding per row.

**What to change.** One paragraph in every review subagent brief: a rough tool-call ceiling per finding (but only where a verification step follows, as in `pr-reviewer` Step 5; `implementation-review` has no verifier behind its subagents, so it gets the write-when-sufficient rule without the number), an instruction to write the finding as soon as the evidence is sufficient rather than continuing to gather, and explicit permission to finish early when a sweep turns up nothing. This directly attacks the padding problem that makes long reviews unreadable.

### 2.3 Explicit permission to find nothing

**What they do.** The plan prompt ends its rules with:

> If the changes carry no identifiable risk at all, output the summary line, then the issues header, then "(none)". Do not invent issues to fill the list.

**What we have.** `implementation-review` guards the opposite failure ("Don't report clean without the subagent actually reading the diff") but never licenses emptiness. Given a seven-row table of things to look for, a subagent under a "prove you read it" instruction will manufacture a row.

**What to change.** Pair the existing guard with its inverse in each brief: a clean check is a legitimate result, and inventing a finding to demonstrate diligence is the worse failure of the two. One sentence.

### 2.4 Splitting context scope from comment scope

**What they do.** The main review prompt separates what you may read from what you may comment on:

> Review every file listed in the review set individually. Cross-file observations within the review set are encouraged: look for inconsistencies, missing updates, and broken contracts across related files. Context tools are for gathering background only. Your comments must address code within the review set; never produce comments targeting files outside it.

**What we have.** Implied, never stated. A subagent told to check SOLID across "the full PR diff" that opens a neighbouring file for context can, and sometimes does, file a finding against the neighbour. On a PR that is a comment anchored to a line the author did not touch.

**What to change.** One sentence per brief: context reading is unbounded, comment targets are bounded to the diff. Note that this pairs with our existing `(introduced)` / `(pre-existing)` marking rather than replacing it: pre-existing findings inside the diff still ship, findings outside the diff do not.

### 2.5 Iterative deepening with a deliberate plan strip

This is the most interesting mechanism in the repo and the one with no analogue in our skills.

**What they do.** Effort level maps directly to review rounds (`internal/config/template/effort.go`: low 1, medium 2, high 3). Each round after the first receives the previous rounds' confirmed findings with a fixed preamble (`internal/agent/util.go`, `buildConfirmedCommentsBlock`):

> The following issues were already identified and confirmed in a prior review pass. Do not repeat them. Continue reviewing all files and report any other real issues you find.

The findings are compressed before injection (path, a truncated code snippet, a truncated issue line, capped at 30) so the feedback block does not eat the budget.

And then the detail that makes it work, from `internal/agent/agent.go:1454`:

```go
// Round 2+ strips the plan to avoid it acting as a coverage ceiling.
roundPlan := planResult
if round > 1 {
    roundPlan = ""
}
```

The risk plan that focused round one is deliberately withheld from round two, because guidance that helps you focus becomes a blinder once you have already covered what it pointed at. That is a genuinely sharp observation about guided review, and it generalizes well beyond OCR.

**What to change.** Offer a second pass on demand, not by default. The shape: rerun the same brief with the surviving findings injected as "already found, do not repeat, keep looking", and with any focusing guidance from the first pass (the plan, the ticket acceptance criteria, the Figma frame list) withheld. Worth prototyping in `pr-reviewer` first, where review depth is worth paying for, before considering it for the pre-commit gate.

### 2.6 Path-scoped project rules

**What they do.** `.opencodereview/rule.json` maps a glob to a rule body, with a `merge_system_rule` flag deciding whether the project rule replaces or augments the built-in checklist. Resolution order is flag, then repo, then home dir, then built-in. Their own repo's single rule is the argument for the mechanism:

> `internal/llm/providers.go`: field values must be inline literals, field order must follow a named sequence, env var naming must match a pattern, protocol must reference a constant. Any provider entry added or changed must be accompanied by updates to the provider table in four named docs files; if docs are not updated in the same PR, flag this as a required change. Every new provider must have a correspondingly named test verifying protocol, base URL, env var and models.

Every one of those is mechanically checkable and none of them is inferable from the diff alone. A reviewer without the rule file will not catch the four-doc sync requirement, because nothing in `providers.go` mentions those docs.

**What we have.** `staleness-audit` does canary-based drift detection (README, decision log, public API, release notes) repo-wide, by inference. It would probably catch "provider added, docs not updated" in a repo where it had already learned that coupling. It cannot be told.

**What to change.** First, the zero-config version: most repos already encode "touch X, update Y" couplings in CLAUDE.md, and `staleness-audit` can read those as rules today. Only once CLAUDE.md gets crowded does a dedicated registry earn its keep. At that point, give `staleness-audit` an optional path-scoped rule registry it reads when present: glob to assertion, where assertions are the mechanical couplings a repo knows about itself (touch this, update that; add one of these, add a test named so). Medium cost, because it is a new config surface with its own resolution order, but it turns the audit's weakest step (guessing the repo's coupling rules) into a lookup. Worth scoping separately.

### 2.7 Semantic file grouping (threshold-gated, if at all)

**What they do.** A dedicated grouping pass clusters changed files before review (`grouping_task_system.md`): same module or feature, producer and consumer pairs such as interface and implementation, i18n or config variants of one resource, files sharing a directory and a concern. Every file lands in exactly one group, maximum ten per group, and files are addressed by integer index rather than path to keep the output cheap and unambiguous.

**Why it matters.** It makes review cost scale with the diff instead of with the diff times the number of concerns, and it puts related files in front of the same reviewer at the same time, which is the only way cross-file contract drift gets caught.

**Why to be careful.** Our fan-out axis is concern (correctness, security, tests, SOLID, clean code), not file. Adding a group axis multiplies agents. For a 20 file PR in four groups that is twenty subagents instead of five.

**What to change, if anything.** Threshold-gated only: when a diff exceeds some size, group first and fan concerns out within the group rather than across the whole diff. OCR's own thresholds are instructive as a model for making this cheap (their plan phase triggers when a single file exceeds 50 changed lines or a group's combined changed lines exceed 100). Propose, do not implement, until someone has felt the pain on a real large PR.

### 2.8 A standing security assurance case

Different artifact class, listed here because it is the highest-ceiling idea in the repo.

**What they have.** `ASSURANCE_CASE.md`: a threat model with actors and their trust levels, an ASCII trust-boundary diagram, a numbered threat table (threat, boundary, mitigation), Saltzer and Schroeder's eight design principles each mapped to a concrete implementation decision, an OWASP Top 10 and CWE Top 25 table with a per-row verdict of Mitigated or Not Applicable and the reason, and an automated verification table naming the tool and when it runs.

**Why it matters to us.** `security-audit` phase one is "understand the repo's security model". Today that means inferring it from the code every run. An assurance case is that model, written down, which changes the audit from inference to comparison: the diff either respects a documented boundary or crosses it, and crossing one is a finding with a citation.

**What to change.** Two separate moves. First, `security-audit` phase one should look for a standing assurance case (or threat model, or security decision record) before inferring one, and should say so in its output when none exists. Second, and independently, `write-docs` could carry an assurance-case template so the skill can produce the artifact it wants to read. Track this separately from the rest of the list.

### 2.9 Anchor recovery when a comment fails to land

**What they do.** A dedicated re-location prompt (`re_location_task_user.md`) runs only when a comment's code snippet fails to match the diff. It is given the diff, the failed snippet and the comment, and must return the minimal contiguous range the comment targets, copied verbatim from the diff with leading markers stripped, no surrounding context, one location if several apply, output as a bare fenced block with no commentary. Downstream, a comment whose line range is still unresolved is reported as `start_line` and `end_line` both zero rather than dropped, and the consuming skill is told to read the comment, find the section by context, and apply it there.

**What we have.** `pr-reviewer` Step 8 requires every comment to anchor on a line added in the diff and says to verify by parsing the hunk headers before posting. There is no instruction for what to do when that check fails, which in practice means the comment is either posted on a wrong line or quietly lost.

**What to change.** A short fallback in Step 8: when a finding will not anchor, re-derive the target range verbatim from the diff, and if it still will not anchor, fold it into the review body rather than dropping it. (GitHub's `subject_type: file` exists only on the standalone comment endpoint, which posts immediately and would bypass the pending-review gate; the batched review endpoint Step 8 uses has no file-level option, so the body is the only in-gate fallback.) Cheap, and it closes the one path by which a verified finding disappears after surviving Step 5.

---

## 3. The one place we should not follow them

OCR's review filter (`review_filter_task_system.md`, `review_filter_task_user.md`) is the best-written prompt in the repo, and it argues for the opposite of what `pr-reviewer` Step 5 does. The disagreement is real and it is positional, not a gap in ours.

**Their filter.** A separate pass that sees only the diffs, not the codebase, and can only remove comments. It opens by stating the cost asymmetry outright:

> Keeping an incorrect comment costs a reviewer a few seconds of attention. Removing a correct comment silently destroys a real finding: it never reaches anyone, and nobody learns it was dropped.

From that it derives exactly two grounds for removal, each requiring a citable diff line: the comment targets code absent from its subject file's diff, or a specific diff line literally contradicts its central claim with no chain of reasoning required. Then a set of protected subjects that are vetoed from removal before correctness is even assessed (memory safety, concurrency, linkage and declaration consistency, behavioral or compatibility change, an unused parameter), justified like this:

> These are the categories where a wrongly removed comment is most expensive, and where your own confidence is least trustworthy, including confidence that the language, compiler, or runtime does not behave the way the comment claims. On a protected subject you do not get to be confident. Approve.

The method is five ordered steps, stop at the first that applies, default approve.

**Ours.** `pr-reviewer` Step 5 rule 4 says the opposite for the same categories: reproduce the concurrency reasoning yourself, state the interleaving that produces the bad outcome, and if you cannot construct it the finding does not ship.

**Why both are right.** OCR's filter is diff-blind and has a human downstream who will triage, so it optimizes recall and forbids itself confidence it has not earned. Our Step 5 verifier has full tool access and its output gets posted on a colleague's PR, where a wrong finding costs the author's time and our credibility, so it optimizes precision. Different position, different loss function, opposite correct answer. Worth naming as a choice in the skill rather than leaving it to look like an oversight.

(Related non-conflict: `implementation-review` Check 7's 80% confidence gate is a bar on *raising* a finding. OCR's proof standard is a bar on *removing* one. Those are different gates pointing the same direction, not a contradiction.)

**What is absorbable from the filter even so.** Two smaller things:

1. **State the cost asymmetry in the prompt.** Our Step 5 says what to do ("kill it if it does not survive") without ever telling the verifier which of its two possible errors is worse. A verifier that has not been told will guess, and the guess drifts run to run. One sentence naming the asymmetry, in whichever direction we choose, stabilizes it.
2. **Require a dropped finding to cite what killed it.** Step 5 says "read the actual code" and Step 7 reports drops one line each, but nothing requires the drop to be evidenced. OCR requires naming the specific diff line that disproves a comment before it can be removed. The same discipline applied to our drops ("dropped: the test it claimed was missing is at `foo_test.ts:44`") makes the drop auditable and makes the reviewer actually look.

---

## 4. What we already do better, so nobody trades it away

OCR's review output is a severity-tagged list of technical findings. Ours is a review a person can receive. The gap is entirely on our side of the ledger and none of it should be given up in exchange for the above:

- **Humanized comment drafting**, with eight before-and-after pairs and a running commentary on what changed in each. OCR has no voice guidance at all.
- **The author-resolvability rule**: a reference the author cannot follow from the page they are on has failed, however precise it is. This has no analogue anywhere in OCR.
- **The `(introduced)` / `(pre-existing)` marking**, which changes framing without changing severity.
- **Testing philosophy as a shared definition** across planning and review, so both sides judge "good test" the same way.
- **The two-artifact split** (chat summary for the user, one-paragraph body for the author) and the anti-point-scoring rules.
- **The approval gate.** Nothing posts without explicit per-message approval.

One inconsistency in their repo worth recording. Both of OCR's own skills instruct the host agent to do exactly what the filter prompt calls the expensive error: `skills/open-code-review-delegate/SKILL.md` (Step 6) says "Discard likely false positives silently", and `skills/open-code-review/SKILL.md` (Step 3) says to present results "discarding low severity items that are likely false positives or nitpicks". The filter prompt's whole thesis is that silent removal on a hunch is the error you cannot detect afterwards. The filter prompt is clearly the considered artifact; the skill text is looser. Read the prompts, not the skill docs.

---

## 5. Ranked proposal

| # | Change | Skill(s) | Cost | Value |
|---|---|---|---|---|
| 1 | Per-subagent coverage line (seen / reviewed / skipped with reason); synthesis refuses a verdict on unexplained partial coverage | `pr-reviewer`, `implementation-review` | Low | High |
| 2 | Tool-call budget per finding, write-on-sufficient-evidence, explicit permission to finish early | all review subagent briefs | Low | High |
| 3 | Explicit "(none) is a valid result, do not invent findings to fill the list" | `implementation-review`, `pr-reviewer` | Low | Medium |
| 4 | Context scope unbounded, comment scope bounded to the diff | all review subagent briefs | Low | Medium |
| 5 | Name the cost asymmetry in Step 5, and require each dropped finding to cite what killed it | `pr-reviewer` | Low | Medium |
| 6 | Secondary-file rule: reviewing an implementation does not cover its interface, config or type counterpart | `pr-reviewer`, `implementation-review` | Low | Medium |
| 7 | Optional second pass: inject surviving findings as "already found, keep looking", withhold round one's focusing guidance | `pr-reviewer` | Medium | High |
| 8 | Read coupling rules from CLAUDE.md first; path-scoped rule registry only if that gets crowded | `staleness-audit` | Low, then Medium | High |
| 9 | Phase one looks for a standing assurance case before inferring the security model | `security-audit` | Medium | High |
| 10 | Assurance-case template so we can produce the artifact in #9 | `write-docs` | Medium | Medium |
| 11 | Threshold-gated semantic file grouping before concern fan-out | `pr-reviewer` | High | Medium |
| 12 | Anchor-recovery fallback when a comment fails to land on an added diff line | `pr-reviewer` | Low | Medium |

Items 1 through 6 and 12 landed on 2026-09-14 as a single editing pass over the subagent briefs, `pr-reviewer` Steps 5, 7 and 8, and `implementation-review` Step 3. Items 7 through 11 each want their own design conversation and are still open.
