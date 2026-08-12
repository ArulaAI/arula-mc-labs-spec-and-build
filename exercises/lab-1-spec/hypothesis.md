---
lesson_id: spec-to-build::lab-1-spec
status: draft
---

# Hypothesis — Lab 1

Fill this in **before** you run `/spec`. It is your pre-tool prediction — the point is to commit to
a guess so you can notice where the tool confirms you, surprises you, or catches something you
missed.

## What I expect is missing or wrong

> Before running anything: read `specs/incremental-auth.spec.md` and `specs/NON_NEGOTIABLES.md`
> yourself. Which sections do you expect are incomplete? Which acceptance criterion looks
> non-testable, and why?

_(your prediction)_

## What edge case a careless spec would miss

> A retry, two concurrent captures, an expired hold, a partial capture that's individually valid
> but invalid in sequence — which of these do you expect the current draft doesn't account for?

_(your prediction)_

## Where I expect spec-craft to be weakest

> `spec-craft` checks structure and testability mechanically. Where do you expect it to accept
> something that's structurally fine but still substantively thin — the kind of gap only a human
> reading for meaning would catch?

_(your prediction)_

**Confidence:** Low / Medium / High — _<rationale>_

---

## Reflection — what actually happened *(fill in AFTER `/spec` reports READY)*

- Where my prediction was **right**:
- Where my prediction was **wrong** or I was surprised:
- Did `spec-craft` catch anything I hadn't noticed? Did I catch anything it didn't flag?
- One thing I now understand about this feature that I didn't before:
