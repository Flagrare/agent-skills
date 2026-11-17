# Research: building and maintaining evals for LLM features

- **Slug:** `2026-11-17-building-and-maintaining-evals`
- **Date:** 2026-11-17
- **Status:** complete
- **Triggered by:** Yuri, after the Knochengeist answer evals: research how to make really good evals, then a reusable skill for creating and maintaining them, with Braintrust as one of the references.
- **Informed:** [`/flagrare:evals`](../../plugins/flagrare/skills/evals/SKILL.md)

## Question

How do the best practitioners create an eval suite for an LLM feature (an in-app assistant, an agent, a prompt-driven feature), and how do they keep it honest over time: when the prompt changes, the model changes, or production finds a new failure?

## Sources

### [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/), [Creating a LLM-as-a-Judge That Drives Business Results](https://hamel.dev/blog/posts/llm-judge/), and the [evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- **Authors / Org:** Hamel Husain; the FAQ with Shreya Shankar
- **Type:** engineering blog
- **Published:** 2024-03-29; 2024-10-29; FAQ page dated 2026-09-18
- **Accessed:** 2026-11-17
- **Relevance:** high
- **What this contributed:** the skill's spine is error analysis before evals:
  - Read 100 or more real traces and write a free-text note on each (open coding).
  - Group the notes into a failure taxonomy with counts (axial coding), and stop when new traces show nothing new.
  - One domain expert owns the pass/fail call.
  - Judges give binary verdicts with a written critique, and are validated against that expert's labels by TPR and TNR on train/dev/test splits.
  - Write evaluators "for errors you discover, not errors you imagine", and fix obvious prompt gaps before building any evaluator.
- **Quoted:**
  > Outsourcing [error analysis] is usually a big mistake.

### [Who Validates the Validators?](https://arxiv.org/abs/2404.12272)
- **Authors / Org:** Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran, Arawjo
- **Type:** academic paper (arXiv preprint)
- **Published:** 2024-04-18
- **Accessed:** 2026-11-17
- **Relevance:** high
- **What this contributed:** *criteria drift*: people need criteria to grade outputs, and grading outputs is what defines the criteria. So rubrics are expected to change after looking at real outputs, and a judge is picked by how well it agrees with a human-graded subset.

### [Evaluating the Effectiveness of LLM-Evaluators](https://eugeneyan.com/writing/llm-evaluators/) and [An LLM-as-Judge Won't Save The Product](https://eugeneyan.com/writing/eval-process/)
- **Authors / Org:** Eugene Yan
- **Type:** engineering blog
- **Published:** 2024-08-18; 2025-04-20
- **Accessed:** 2026-11-17
- **Relevance:** medium
- **What this contributed:**
  - Pairwise comparison for subjective qualities, direct binary scoring for objective ones.
  - Precision and recall over correlation.
  - Watch for position, verbosity and self-enhancement bias.
  - Aim for a balanced pass/fail label set.

### [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), [A statistical approach to model evaluations](https://www.anthropic.com/research/statistical-approach-to-model-evals)
- **Authors / Org:** Anthropic (Grace, Hadfield, Olivares, De Jonghe; Evan Miller for the statistics paper)
- **Type:** engineering blog, vendor docs, research
- **Published:** 2026-01-09; undated; 2024-11-19
- **Accessed:** 2026-11-17
- **Relevance:** high
- **What this contributed:**
  - **Terms:** task, trial, transcript, outcome.
  - **Size:** start from 20 to 50 tasks drawn from real failures, each with a reference solution.
  - **Graders:** code first, then a model, then people. Grade outcomes, not paths. Give judges an "Unknown" option. Test both the cases where a behavior should happen and where it shouldn't.
  - **Consistency:** pass^k for consistency, pass@k for "can it ever".
  - **Two suites:** capability sets (start low) apart from regression sets (near 100%). A 0% pass rate usually means a broken task.
  - **Statistics:** standard errors and 95% confidence intervals, paired differences when comparing two versions, and a power analysis to size the set.

### Braintrust: [quickstart](https://docs.braintrust.dev/start/eval-sdk), [writing scorers](https://docs.braintrust.dev/evaluate/write-scorers), [comparing experiments](https://docs.braintrust.dev/evaluate/compare-experiments), [best practices](https://docs.braintrust.dev/evaluate/best-practices), [online scoring](https://docs.braintrust.dev/evaluate/score-online), [datasets](https://docs.braintrust.dev/annotate/datasets), [Measuring what matters](https://www.braintrust.dev/blog/measuring-what-matters), [eval-driven development](https://braintrust.dev/articles/eval-driven-development), [How to evaluate LLMs and agents in production](https://www.braintrust.dev/articles/how-to-eval), [autoevals](https://github.com/braintrustdata/autoevals)
- **Authors / Org:** Braintrust (Carlos Esteban for Measuring what matters)
- **Type:** vendor docs and blog
- **Published:** docs undated; 2025-10-10; 2026-02-18; 2026-05-16
- **Accessed:** 2026-11-17
- **Relevance:** high
- **What this contributed:** the vocabulary and the loop the skill uses:
  - **An eval is data, a task and scorers (0 to 1)**, and each run is an experiment compared against a baseline, case by case, with improvements and regressions shown per row.
  - **Scorers:** one per dimension, binary to start, written to fail at first, and tested on known good and bad cases.
  - **Datasets:** versioned, grown from production failures.
  - **Online scoring:** samples production traces (1 to 10% at high volume, up to 100% for critical features) and feeds new cases back.
  - **CI:** eval thresholds decide whether a change can ship ("eval-driven development"). Differences under 5 points deserve caution.

### [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [graders](https://developers.openai.com/api/docs/guides/graders)
- **Authors / Org:** OpenAI
- **Type:** vendor docs
- **Published:** undated
- **Accessed:** 2026-11-17
- **Relevance:** medium
- **What this contributed:**
  - The named anti-patterns: generic metrics, biased design, vibe-based evals, ignoring human feedback.
  - "Log everything", so production can be mined for cases.
  - Tool-choice and argument checks for agents.
  - The OpenAI Evals platform goes read-only on 2026-10-31 and shuts down on 2026-11-30, so the skill depends on no hosted platform.

### Tools: [promptfoo](https://github.com/promptfoo/promptfoo), [Inspect AI](https://inspect.aisi.org.uk/), [LangSmith](https://docs.langchain.com/langsmith/evaluation-concepts), [Arize Phoenix](https://github.com/Arize-ai/phoenix), [DeepEval](https://github.com/confident-ai/deepeval)
- **Authors / Org:** promptfoo (now part of OpenAI, per its repo); UK AISI and Meridian Labs; LangChain; Arize; Confident AI
- **Type:** open-source projects and docs
- **Published:** ongoing
- **Accessed:** 2026-11-17
- **Relevance:** low
- **What this contributed:** the short "if the project already uses one of these" list in the skill. The workflow doesn't depend on any of them.

### Our own field test: Knochengeist answer evals (2026-11-17)
- **Type:** first-hand
- **Relevance:** high
- **What this contributed:** the first baseline read 49 of 90 runs passed, and most of the failures were the graders, not the answers:
  - **The names check was wrong.** It flagged real methods like `add_child` and `_ready`, plus the answer's own example names (`take_damage`, an action called `"move_left"`). Fixed and re-graded from the saved runs, the score was 75 of 90, with no new questions asked.
  - **The test harness was wrong.** It typed the wanted node into every search box, even when a step said to type "Node" first.
  - **Two rubrics were wrong.** They assumed code answers to questions an editor helper fairly reads as editor tasks.

  Code graders need the same validation on real outputs as LLM judges. And saving every run's raw output is what makes re-grading cheap.

## Synthesis

**Creating a suite:**
1. Look at real traces first: open coding, then axial coding into a failure taxonomy.
2. Have one owner of the pass/fail call.
3. Fix obvious prompt gaps.
4. Write one evaluator per failure mode that keeps coming back: code where it can decide, a binary judge only where it can't.
5. Validate every grader (code checks too) on real outputs, and judges by TPR and TNR against the owner's labels.
6. Cover both directions of each behavior, keep capability and regression sets apart, and run k trials.
7. Record a baseline with confidence intervals.

**Maintaining one:**
- **Every change:** runs the regression set against the baseline, read case by case.
- **A model upgrade:** reruns everything with paired differences, and re-validates the judges.
- **A production failure:** becomes a case, and a new scorer if it's a new failure mode.
- **On a schedule:** fresh error analysis, graduation of saturated capability tasks, and retirement of evals that tell you nothing.

**Where the sources disagree:**
- **Scales.** Anthropic's docs show a 1 to 5 scale; Husain, Yan and OpenAI argue for binary. The skill takes binary per dimension, which still allows several dimensions.
- **Off-the-shelf metrics.** Braintrust starts from autoevals; Husain warns against generic metrics. The skill allows them only once error analysis shows they match a real failure.
- **Starting size.** It ranges from 5 to 200. The skill says 20 to 50 tasks, mined from 100 or more traces.

## Downstream uses

- [`/flagrare:evals`](../../plugins/flagrare/skills/evals/SKILL.md)
