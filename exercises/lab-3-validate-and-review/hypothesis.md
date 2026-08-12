---
lesson_id: spec-to-build::lab-3-validate-and-review
status: draft
---

# Hypothesis — Lab 3

Fill this in **before** you dispatch `code-to-spec-validator`. You already have a belief, from
Lab 2's reflection, about whether your remaining-amount check is correct. Now predict what happens
when something with no memory of writing it looks at the diff.

## Which check I expect to catch it

> Three things could catch a wrinkle in your capture-amount check: your own test-writing in Lab 2,
> `code-to-spec-validator` here, or `pr-reviewer` here. Which do you predict actually catches it
> (or confirms there's nothing to catch), and why?

_(your prediction)_

## Where I expect a fresh-context subagent to be more useful than me

> `code-to-spec-validator` and `pr-reviewer` never see why you wrote the code the way you did —
> only what it does. Where do you expect that lack of context to help rather than hurt?

_(your prediction)_

**Confidence:** Low / Medium / High — _<rationale>_

---

## Reflection — what actually happened *(fill in AFTER both Stage 4 and Stage 5 are closed)*

- Did the wrinkle show up in your Lab 2 implementation? If yes, which checkpoint actually caught
  it — your own test, the validator, or the reviewer?
- Where my prediction was **right**:
- Where my prediction was **wrong** or I was surprised:
- One thing I now understand about fresh-context review that I didn't before:
