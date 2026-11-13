# Evals

Test cases for the skills. **Dev-only** — not shipped to users, and not part of any `.skill` bundle.

## Why

Skill behaviour is defined in plain markdown. Plain markdown drifts, and a payment skill that drifts writes wrong hashes. Evals exist to:

1. Catch regressions after a `SKILL.md` edit — signing order, status codes, sandbox vs live URLs, plan gates.
2. Prove a new gateway earns its place: the same three questions, scored with and without the skill.
3. Onboard contributors. Reading three worked cases is faster than reading every reference file.

The number that matters is the **gap** between with-skill and without-skill. A skill that scores 100% while the base model also scores 100% is not earning its tokens.

## Anatomy of a case

```
evals/<skill>/<case-name>/
├── prompt.md          the user request, verbatim
├── case.yaml          schema_version, name, expected_outcome
└── graders/
    ├── 01-some-check.md
    └── 02-another-check.md
```

Each grader is one checkable fact, pass or fail, written so two people would score it the same way. Grade the *answer*, not the process: "is the amount formatted with two decimals" is a grader; "did it read `checkout-api.md`" is not.

`python scripts/verify.py` fails if a case is missing `prompt.md`, `case.yaml` or graders, so the structure is enforced even when nobody runs the cases.

## Running a round

There is no runner. A round is manual and takes about an hour per skill.

1. Pick a commit. Note the SHA.
2. For each case: start a **fresh** session with the skill installed, paste `prompt.md`, save the answer.
3. Repeat in a fresh session **without** the skill (or with skills disabled), same prompt.
4. Score each grader for both answers. A grader passes only if the answer states the fact correctly; "implied by the code" counts only if the code is right.
5. Record the round in `docs/benchmarks/<skill>-iteration-<n>.md` using the template below.
6. Give each answer a time and token count. A pass that takes 4× longer is a regression even at 100%.

Do not let the with-skill answer see the graders, and do not fix a case mid-round. If a case is broken, note it and rerun the whole round after fixing.

## What to record

`docs/benchmarks/<skill>-iteration-<n>.md`:

```markdown
# Skill Benchmark: <skill>

**Model**: <model name and id>
**Date**: <ISO 8601>
**Evals**: <case>, <case>, <case> (1 run each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | ... | ... | ... |
| Time | ... | ... | ... |
| Tokens | ... | ... | ... |
```

Then one short paragraph on **what the without-skill answers got wrong** — invented endpoints, a made-up signature scheme, a declined status read as success, a skipped webhook check. That paragraph is the useful part of the benchmark; the percentages are noise without it.

State the sample size honestly. Three questions, one run each, is a strong signal, not a guarantee.

## When to add a case

Add one when:

- A bug reached a user or a reviewer and only manual testing caught it.
- A new gateway or reference file ships. Three cases is the minimum: one code task, one support question, one gotcha the model usually misses.
- A gateway changes its docs in a way that would flip an answer.

Don't add cases that test internals ("did it read the reference file", "did it call the helper script"). Test what the user sees.

## Rules

- **Facts come from the gateway's public docs.** A grader that asserts something the docs don't say is a bug in the eval.
- **Include the gotchas.** The best cases are the ones where the base model is confidently wrong: OnePay's unsigned callback, Genie's body-less signature, Koko's field order, WebXPay's signature recovery.
- **Never put real credentials in a prompt.** Use placeholders; the skills are written to expect them.
- **Regressions win.** If scores drop more than roughly 15% on pass rate, or time more than doubles, investigate the edit before shipping it.

See [docs/adding-a-gateway.md](../docs/adding-a-gateway.md) for the whole contribution flow.
