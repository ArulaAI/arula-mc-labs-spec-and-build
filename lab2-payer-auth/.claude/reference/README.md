# Reference / recovery states — FACILITATOR ONLY

`reference_guard.py` denies Read, Edit, Write and Bash access to everything under this directory
unless `WORKBENCH_FACILITATOR=1` is set. A learner session cannot open any of it.

## Restoring a stage

```bash
export WORKBENCH_FACILITATOR=1
# copy only what the group needs, then:
unset WORKBENCH_FACILITATOR
```

| Path | Recovers | Restore to |
|---|---|---|
| `stage1-context/target-pass-proxy.context.md` | Stage 1 | `.claude/context/target-pass-proxy.context.md` |
| `stage2-spec/retrieve-payer-auth.spec.md` + `.status.json` | Stage 2 | `boost-authentication-service/specs/` |
| `stage3-plan/issues.json`, `plan.md` | Stage 3 | `boost-authentication-service/issues.json`, `docs/plans/plan.md` |
| `stage4-tests/auth-service/*.java` | Stage 4 | `boost-authentication-service/src/test/java/com/mastercard/pgs/auth/` |
| `stage4-tests/order-processing/*.java` | Stage 4 | `boost-order-processing/src/test/java/com/mastercard/pgs/orders/` |
| `stage4-tests/tdd-log.md` | Stage 4 | `boost-authentication-service/docs/tdd-log.md` |
| `stage5-validation/` | Stage 5 | expected validator output, the smallest fix, `docs/validation-log.md` |
| `stage6-solution/boost-authentication-service/src/…` | Stage 6 | overwrite the matching files in the repo |
| `stage6-solution/boost-order-processing/src/…` | Stage 6 | overwrite the matching files in the repo |
| `stage6-solution/docs/PR_DESCRIPTION.md` | Stage 6 | `boost-authentication-service/docs/PR_DESCRIPTION.md` |
| `trap-wrong-impl.patch` | grading anti-gaming probe | applied by `grade_repo.py` to a temp copy only |

## Stage 1 note

`repo-context-compressor` does not exist in the current Workbench (see
`Workbench_Issues_To_Address.md`, L2-1). If it is still absent on session day, hand the group
`stage1-context/target-pass-proxy.context.md` at the start of Stage 1 and have them read it —
Stage 1's reading and human gate are unchanged; only the generation step is provided rather than
run.

## Solution overlay — full restore

```bash
export WORKBENCH_FACILITATOR=1
cd "$WORKSPACE/.claude/reference/stage6-solution/boost-authentication-service"
find src -type f -name '*.java' -exec cp {} "$WORKSPACE/boost-authentication-service/"{} \;
cd "$WORKSPACE/.claude/reference/stage6-solution/boost-order-processing"
find src -type f -name '*.java' -exec cp {} "$WORKSPACE/boost-order-processing/"{} \;
unset WORKBENCH_FACILITATOR
```

The solution adds `AuthenticationRecordNotFoundException` and `MalformedRequestException`, which
do not exist in the starter — the `find` above copies them in.

## Do not

- Do not copy anything from here into a learner tree before that group has reached the stage.
- Do not read the completed spec aloud in Stage 2; the wording of AC-3 (AC-INCOMPLETE) is the
  answer to the stage's human gate.
