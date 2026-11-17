---
name: evals
description: "Create and maintain evals for an LLM feature (an in-app assistant, a chatbot, an agent, any prompt-driven feature): error analysis on real outputs first, one binary grader per failure mode (code where it can decide, a validated judge where it can't), k trials with pass^k and confidence intervals, a saved baseline, and the upkeep loop (every prompt or retrieval change, every model upgrade, every production failure, a scheduled review). Grounded in Hamel Husain and Shreya Shankar's error-analysis method, Anthropic's agent-eval guidance, Braintrust's dataset/task/scorer/experiment loop, Eugene Yan and OpenAI. Use when the user says 'evals', 'eval suite', 'measure the answers', 'is the AI getting better', 'LLM judge', 'golden set', 'regression test for prompts', 'benchmark our assistant', when a prompt, model or retrieval change needs proof it helped, when a production answer was wrong and should never happen again, or when an existing eval suite needs a check-up."
---

# Evals

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

An eval is how you know an LLM feature got better instead of hoping it did. It's a set of real tasks, run the way users run them, graded so that a number moves when quality moves, and so that every failed case says why. This skill builds one from nothing, and keeps one honest as the prompt, the model and the product change. (Grounded in [`docs/research/2026-11-17-building-and-maintaining-evals.md`](../../../../docs/research/2026-11-17-building-and-maintaining-evals.md).)

**REQUIRED BACKGROUND:** `/flagrare:testing-philosophy`. An eval is a test of behavior a user observes: grade the outcome, never the path the model took to it.

---

## Words this skill uses

- **Task**: one input the feature gets, with what a good result must do. **Trial**: one attempt at a task. **Run**: every task's trials, saved together. (Anthropic's terms; Braintrust calls a run an *experiment*.)
- **Grader** (Braintrust: *scorer*): turns one trial into pass or fail with a reason. A **code grader** decides from the output itself; a **judge** is a model given a rubric.
- **pass^k**: a task passes only if all k trials pass. It measures consistency, what users feel. **pass@k**: at least one of k passes. It measures capability.
- **Capability set**: tasks the feature can't do reliably yet; it starts low. **Regression set**: tasks it must keep doing; it sits near 100%.
- **Baseline**: the saved run every later run is compared with, task by task.

---

## The hard rules

These come from the sources in the research file, and each one has burned someone.

1. **Read real outputs before writing any eval.** Graders are for errors you found, not errors you imagined. (Husain)
2. **One named person owns pass/fail.** A domain expert, not a committee and not the agent. (Husain)
3. **Binary verdicts, one per dimension.** Never a 1 to 5 scale; split a quality into yes/no checks instead. (Husain, Yan, Braintrust)
4. **Code graders first; a judge only where code can't decide.** Code is cheap, fast and repeatable. (Anthropic, Husain)
5. **Validate every grader on real outputs before trusting its number.** That includes code graders, and judges get TPR and TNR against the owner's labels. (Husain, Shankar; field test below)
6. **Save every trial's raw output.** Then a grader or rubric fix re-grades the saved run without asking the model again.
7. **Grade the outcome, not the path, and test both directions** (cases where the behavior should happen and where it shouldn't). (Anthropic)
8. **Run k trials, and report pass^k and a confidence interval.** One trial of a nondeterministic system is an anecdote. (Anthropic)
9. **Keep capability and regression sets apart.** A 100% capability set needs harder tasks; a 0% task is usually broken. (Anthropic, Husain)
10. **Every production failure becomes a task.** A new kind of failure also gets its own grader. (Braintrust, Husain)
11. **Change one thing per run, and pin what was run:** the dataset version, the prompt hash, the model. (Braintrust)
12. **No generic metric as a gate.** BLEU, ROUGE, "helpfulness 1 to 10" or cosine similarity only count when error analysis shows they track a real failure. (Husain, OpenAI)

---

## Creating a suite

### Step 1: Pin down what's being evaluated

Name, in one or two sentences:
- **The feature:** what it does, who uses it, and what a good result lets them do.
- **The surface:** where it runs, for example "the in-editor helper, through the user's own Claude Code" or "the support bot's `/answer` endpoint".
- **The owner:** the one person whose pass/fail call is final (rule 2). If the user doesn't name one, the user is the owner.
- **The budget:** trials cost money or plan usage. Say what one full run costs (tasks x trials x calls per trial) before running it, and ask when it's real money or someone's plan limit.

### Step 2: Error analysis on real outputs

This is the step everyone wants to skip, and it's the one the rest depends on.

1. **Gather traces.** Aim for 100 or more real inputs with the feature's real outputs: from production logs, support tickets, or a beta. With no traffic yet, write varied inputs along a few dimensions (feature x scenario x persona) and run them through the real feature.
2. **Open coding.** Read each trace. Write one free-text note on what went wrong, or "fine". No categories yet.
3. **Axial coding.** Group the notes into failure modes with counts ("names a method that doesn't exist: 9", "answers an editor question with code: 4"). Stop reading when new traces add no new modes.
4. **Fix the obvious first.** A failure caused by a missing instruction or a bad example in the prompt is fixed before any grader is written.
5. **Show the taxonomy to the owner**, and let them reword it. Criteria change once people look at outputs; that's expected (Shankar's *criteria drift*), not a failure.

### Step 3: Write the tasks

- **Start with 20 to 50 tasks**, mostly from step 2's failures plus the common cases.
- **Each task carries:** an id, the input, the version of whatever it depends on (a framework version, a product plan), its kind, and what a good result must do. Add a reference answer where one exists.
- **Cover both directions:** tasks where the feature should act, and tasks where it should refuse, say "that doesn't exist", or do nothing.
- **Mark each task capability or regression.**
- **Store tasks as data** (JSON or YAML in the repo), versioned with the code.

### Step 4: Write one grader per failure mode

Pick the cheapest grader that can decide:

| What you're checking | Grader |
|---|---|
| Output shape, a required field, a forbidden phrase, a length limit | Code: parse and assert |
| Names, APIs, IDs, links the answer uses really exist | Code: check against the real source (the product's own symbol table, schema or docs) |
| The task got done (a file written, a node in the scene, a row in the DB, a test passing) | Code: check the end state of the environment |
| Facts that match a reference answer | Code if it's exact; else a judge with the reference in its prompt |
| Tone, clarity, whether it answered what was asked | A judge, binary per rubric line |
| Which of two versions is better on a subjective quality | A pairwise judge (Yan), with the order randomized |

Rules for judges:
- **One judge prompt per dimension**, with yes/no per rubric line. Give it the question, the output, and any reference, and ask for JSON only.
- **Allow "unknown".** A reply that isn't the JSON asked for is a failure with a reason, never a silent pass.
- **Watch the biases:** position (randomize the order in pairwise), length (say length doesn't matter), and its own model's style (prefer a different or stronger judge model when it matters).

Every grader returns `{ name, passed, why }`. The `why` is what a person reads to decide whether the grader or the feature is wrong.

### Step 5: Validate the graders

A grader whose number you haven't checked is a guess.

- **Code graders:** run them on the saved real outputs from step 2, then read every failure. Each one is a real failure, or the grader's fault (a false alarm on a real method name, a file name, a name the output made up for its own example). Fix the grader until every failure it reports is real.
- **Judges:** the owner labels 50 to 100 outputs pass/fail with a one-line critique. Split them about 20% to tune the prompt, 40% to check it, and 40% held back for one final test. Report **TPR** (it passes what the owner passes) and **TNR** (it fails what the owner fails), not raw agreement: raw agreement looks great on lopsided labels. Below about 60 labels, the numbers are too noisy to trust.

### Step 6: Build the runner

The runner runs each task k times through the **real feature**, the way a user would. That means the real prompt, the real retrieval and the real UI path where possible, not the model called directly. Each trial is graded, and everything is saved.

- **Saved per trial:** the raw output, any intermediate steps, the time taken, every grader's verdict and reason.
- **Saved per run:** the date, the model, the prompt hash, the dataset version and k.
- **A short table per run:** pass rate, pass^k and median time per task, with the failure reasons, compared with the baseline task by task.
- **Re-grade:** recompute the code graders on a saved run, and re-judge only the tasks whose rubric changed. This is what makes grader fixes cheap (rule 6).
- **Re-ask a few:** run only some tasks again and put them into a saved run (`--only`, `--into`).
- **Test the runner itself** with a stand-in model, in the normal test suite: a short run writes the right verdicts, a bad name fails the names check, a malformed judge reply fails with its reason.

If the project already uses an eval tool (Braintrust, promptfoo, Inspect AI, LangSmith, Phoenix, DeepEval), build on it instead: the same rules apply, with its datasets, scorers and experiments. Don't introduce a hosted platform for a small suite. The plain-files version above is enough, and it stays readable in git.

### Step 7: Record the baseline

1. **Run** every task at k=3 (k=5 when consistency is the product), against the current feature, with no changes.
2. **Read every failure** before saving it. A failure the grader caused gets the grader fixed and the run re-graded (step 5), not frozen into the baseline.
3. **Save** it as the baseline, with its table, and commit both.
4. **Report** the pass rate with a 95% confidence interval, pass^k, and the three biggest failure modes. A real failure the baseline found (a bug in the feature) gets a ticket through `/flagrare:ticket-creator`.

For the interval, a rough one is enough: with n trials and pass rate p, the margin is about `1.96 x sqrt(p(1-p)/n)`. Below 5 points of difference between two runs, say "no clear change".

---

## Maintaining a suite

| When | Do |
|---|---|
| **The prompt, retrieval or grader changes** | Run the regression set (or the whole suite, when small) against the baseline. Read it task by task: a flat average can hide one task fixed and another broken. Ship only when nothing that passed now fails, and say so in the PR with the table. |
| **The model changes** (a new version, or a switch) | Run the full suite at k trials, and compare it with paired differences per task. Re-validate the judges on the held-back labels before trusting their verdicts. Then save a new baseline. |
| **Production gets an answer wrong** | Add the input as a task, with the owner's verdict. If it's a new kind of failure, add a grader for it and validate that grader (step 5). |
| **On a schedule** (monthly, or each release) | Read a fresh sample of 30 to 50 production traces (step 2 again). Graduate capability tasks that pass at pass^k into the regression set. Retire or harden tasks that pass every time and tell you nothing, and drop expensive judges first. |
| **A task always fails** | Read its trials before believing it. A 0% task is more often a broken task or grader than an incapable feature. |
| **Before each push** | A cheap line: if the prompts changed since the latest saved run, say so. It never blocks the push, because a run costs money or plan usage and that's the owner's call. |

---

## Anti-patterns

- **Writing the set from imagination.** Tasks nobody saw fail test what you expect, not what happens.
- **A judge-only suite.** It's expensive, slow, and noisy where code would be exact.
- **Trusting the first baseline number.** Field-tested the hard way, on the Knochengeist answer evals (2026-11-17). The first baseline read 49 of 90. Most of the failures were the graders:
  - a names check that flagged real methods (`add_child`, `_ready`) and the answer's own example names;
  - a test harness that typed the wrong thing into a search box;
  - two rubrics that assumed code answers to questions an editor helper fairly answers with clicks.

  Re-graded from the saved runs, with no new questions, it was 75 of 90. The real bugs it found then stood out clearly.
- **Likert scales.** "Rate helpfulness 1 to 5" gives numbers nobody can act on, and judges drift on them.
- **Raw agreement on lopsided labels.** A judge that always says "pass" agrees 90% of the time with a set that's 90% passes.
- **Averages without task-by-task diffs.** One regression hides behind one fix.
- **Tuning the prompt until the set passes.** Keep a held-back slice nobody tunes against, and keep adding fresh production failures.
- **Running every eval on every push.** Expensive evals run when what they measure changed, or on demand. Cheap code checks can run always.
- **Depending on a hosted eval platform for a small suite.** Plain files in the repo survive vendor changes (OpenAI's Evals platform shut down on 2026-11-30).

---

## Hand-off

End with a short message to the user:
- **Where it lives:** the suite, the runner command, and the baseline file.
- **The numbers:** pass rate with its interval, and pass^k.
- **What's failing:** the top three failure modes, each with a ticket when it's a real bug.
- **What's next:** what to run, and when (the maintenance row that applies).
- **What isn't covered yet:** judges not yet validated against human labels, kinds of input not in the set, any production sampling not set up.
