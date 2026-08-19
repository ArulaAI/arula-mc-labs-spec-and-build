# Lab 2 — The Call You Must Not Make Twice

**Open Claude Code at this directory.** It is the project root for the whole lab.

```
arula-mc-labs-spec-and-build/
  .claude/                                 shared lab config for the workspace
    settings.json                          lab-local hooks
    lab.json                               lab metadata + rubric pointer
    commands/hand-off.md                   /hand-off (lab-local)
    rubrics/lab-2.yaml                     Layer A — journey completeness
    scripts/grade_repo.py                  Layer B — repo state and behaviour
    scripts/journey_event.py               records stage boundaries in the journey
    scripts/validate_spec.sh               runs the plugin's spec validator, wherever it is installed
    scripts/bootstrap_workspace.sh         gives each owned repo its own git history (idempotent)
    hooks/reference_guard.py               protects the answer material
    hooks/pr_gate_guard.py                 blocks the PR artifact while gates are red
    hooks/pan_gate.py                      blocks a write that would add a PAN or secret
    context/                               compressed context for the legacy edge (ships; audited in Stage 1)
    reference/                             facilitator answer + recovery states, incl. the
                                           facilitator key (guarded by reference_guard.py)
  boost-authentication-service/            owned repo — the producer (port 8081)
  boost-order-processing/                  owned repo — the consumer (port 8080)
  journey/                                 created at runtime by the plugin's journey hooks
  ARCHITECTURE.md                          the intended architecture, in nine views
  README.md                                this file
```

**Start here:** `boost-authentication-service/LAB_ACTION_GUIDE.md`

`target-pass-proxy`, the legacy Target/PASS edge, is deliberately **not** in this workspace. It is
represented by a compressed context artifact that ships with this repo at
`.claude/context/target-pass-proxy.context.md`, which you audit in Stage 1.

`mvn test` is green in both owned repos on a fresh clone.

**Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) — system context, component boundaries,
request flow, trust boundaries and the verification layers.

## Distribution

The lab's architecture is **one workspace root, two independently owned repositories, and a
legacy edge that is not in the workspace at all**:

| Part | What it is | Git |
|---|---|---|
| `arula-mc-labs-spec-and-build/` | the workspace root — shared `.claude/` config, hooks, rubric, grader, guarded reference states | its own repo |
| `boost-authentication-service/` | owned repo — the producer, where the work and the trap live | its own repo, own history, committed baseline |
| `boost-order-processing/` | owned repo — the consumer | its own repo, own history, committed baseline |
| `target-pass-proxy` | the legacy Target/PASS edge | **no repo, no source, not in the workspace** — represented solely by `.claude/context/target-pass-proxy.context.md` |

The repo boundary is not decoration. `boost-order-processing` may only rely on what the shared
`openapi/payer-authentication-v1.yaml` promises, and `boost-authentication-service` may only rely
on what the compressed context states about the legacy edge. `ContractConsumerTest` fails if the
two contract copies drift apart.

### Getting the workspace onto a machine

Both routes below produce exactly the architecture in the table above.

**A. From the distribution bundle (what this repository is).** One clone carries all three
parts; a single idempotent script then gives each owned repo its own git history:

```bash
git clone <this-repo> lab2-payer-auth
cd lab2-payer-auth
.claude/scripts/bootstrap_workspace.sh
```

**B. From three remotes (the closest match to how a real squad works).** Publish the workspace
scaffold and each owned repo to its own remote, then have participants clone them side by side:

```bash
git clone <workspace-remote> lab2-payer-auth
cd lab2-payer-auth
git clone <auth-service-remote> boost-authentication-service
git clone <order-processing-remote> boost-order-processing
```

Either way, **each owned repo must have a committed baseline before a learner touches it.** The
PAN/secret gate diffs the working tree against `HEAD`; without a `HEAD` to diff against, it
reports "skip" and silently protects nothing for the whole session. `bootstrap_workspace.sh`
guarantees this for route A; route B gets it from the remotes themselves.

Open Claude Code at the workspace root — never at one of the owned repos. The shared `.claude/`,
the hooks and the grader all resolve from there, and `journey/` is written there.
