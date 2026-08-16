# Lab 2 — The Call You Must Not Make Twice

**Open Claude Code at this directory.** It is the project root for the whole lab.

```
lab2-payer-auth/
  .claude/                                 shared lab config for the workspace
    settings.json                          lab-local hooks
    lab.json                               lab metadata + rubric pointer
    commands/hand-off.md                   /hand-off (lab-local)
    rubrics/lab-2.yaml                     Layer A — journey completeness
    scripts/grade_repo.py                  Layer B — repo state and behaviour
    scripts/journey_event.py               records stage boundaries in the journey
    hooks/reference_guard.py               protects the answer material
    hooks/pr_gate_guard.py                 blocks the PR artifact while gates are red
    hooks/pan_gate.py                      blocks a write that would add a PAN or secret
    context/                               the Stage 1 compressed context lands here
    reference/                             facilitator answer + recovery states (guarded)
  boost-authentication-service/            owned repo — the producer (port 8081)
  boost-order-processing/                  owned repo — the consumer (port 8080)
  journey/                                 created at runtime by the plugin's journey hooks
```

**Start here:** `boost-authentication-service/LAB_ACTION_GUIDE.md`

`target-pass-proxy`, the legacy Target/PASS edge, is deliberately **not** in this workspace. It is
represented by a compressed context artifact you produce in Stage 1.

Each owned repo is its own git repository with a committed baseline. `mvn test` is green in both
on a fresh clone.

Companion document: `Workbench_Issues_To_Address.md` — plugin gaps this lab works around, with
the lab-local mitigation for each.

## Distribution

Three git repositories make up the lab: this workspace scaffold (`.claude/`, the guides, the
companion issues doc) and the two owned service repos. Participants clone the workspace, then
clone both service repos into it side by side, so the layout above is reproduced exactly. Each
service repo carries a committed baseline before distribution — that is what makes `git diff HEAD`
meaningful from a learner's first edit, and the PAN gate is a no-op without it.
