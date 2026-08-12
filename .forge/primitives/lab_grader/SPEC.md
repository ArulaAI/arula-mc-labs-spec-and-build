# U2: /lab-grader — Forge primitive contract

## Purpose

Evaluate a lab session against a rubric defined in `.forge/grader.yaml`. Emit a structured score (JSON + markdown breakdown), write `grade.json` to the journey directory, and append a `lab_grader_run` event to the session JSONL.

## Layer

L2 Universal (every modernized Forge lab MUST ship this primitive — see Project 2 §4.2).

## Inputs

- `lab_root` (positional) — path to the lab root directory. Default: current working directory.
- `--run-id` (optional) — run identifier for the session being graded. If omitted, reads from `.forge/.current-run-id`. Falls back to `run_unknown` if the file is absent.
- `--format` (optional) — `json`, `markdown`, or `both` (default: `both`).
- `--rubric` (optional) — path to the rubric YAML. Default: `<lab_root>/.forge/grader.yaml`.

## Outputs

- **stdout:** JSON score struct and/or markdown breakdown per `--format`.
- **exit code:** 0 if grading succeeded (even if score is low); 1 on rubric parse error or unrecoverable evaluator failure.
- **`grade.json` artifact:** written to `.forge/journey/<run-id>/grade.json` containing `GradeResult` fields.
- **`lab_grader_run` event:** appended to `.forge/journey/<run-id>.jsonl` per Spec A §8.2.

### `GradeResult` structure

```json
{
  "run_id": "run_abc123",
  "lab": "test-fixture-passing",
  "total_score": 72.5,
  "max_score": 100,
  "percentage": 72.5,
  "criteria_results": [
    {
      "id": "build-passes",
      "title": "Build command exits 0",
      "weight": 30,
      "passed": true,
      "points_earned": 30.0,
      "detail": "exit code 0"
    }
  ]
}
```

## Rubric DSL (`grader.yaml`)

The rubric lives at `.forge/grader.yaml` in the lab root. It is parsed by `primitives/lab_grader/shared/grader.py` using Pydantic v2 discriminated unions on the `evidence.type` field.

### Top-level structure

```yaml
lab: <lab-slug>
forge_primitives_version: "0.1.0"
total_points: 100
criteria:
  - id: <unique-slug>
    title: <human-readable name>
    weight: <integer points out of total_points>
    evidence: <evidence block>
```

### Evidence types

All 7 evidence types are listed below. The `type` field is the discriminator.

| Type | Description | Key fields |
|---|---|---|
| `shell` | Run a shell command; check exit code (and optionally stdout/stderr). | `cmd`, `expect_exit`, `timeout_s` (default 120) |
| `file-exists` | Assert a file exists at a path relative to `lab_root`. Optionally check content. | `path`, `content_check.contains`, `content_check.min_length` |
| `failure-mode-clean` | Run U1 `/failure-mode-audit` on a target path; assert no findings above threshold. | `target` (path), `modes` (list, default all), `max_severity` (low/medium/high/critical) |
| `journey-event-present` | Assert that the session JSONL contains at least one event matching a type + optional field predicate. | `event` (type string), `where` (dict of field equality checks), `occurrences_min` (default 1), `before` (event type that must appear after) |
| `llm-judged` | Pass a prompt file + session excerpt to the grader LLM; extract numeric score from JSON response. Passes if score >= 50% of `scoring` max. | `rubric` (path to rubric text file), `input` (path pattern, `<run-id>` substituted), `scoring` (e.g. `"0-20"`), `model_logical` (default `"grader"`) |
| `primitive-authored` | Assert the lab has L3 per-lab primitives under `.forge/local/primitives/`. | `min_count` (default 1), `primitive_name` (prefix filter), `primitive_kind` (`skill` checks for `SKILL.md`, `hook` checks for `*.sh`) |
| `compound` | Logical combinator: AND or OR over a list of child evidence blocks. | `op` (`AND` or `OR`), `children` (list of evidence blocks, same schema) |

### Full rubric example

```yaml
lab: my-lab
forge_primitives_version: "0.1.0"
total_points: 100
criteria:
  - id: build-passes
    title: Build command exits 0
    weight: 20
    evidence:
      type: shell
      cmd: "make build"
      expect_exit: 0

  - id: readme-exists
    title: README present and non-trivial
    weight: 10
    evidence:
      type: file-exists
      path: README.md
      content_check:
        min_length: 100

  - id: no-security-issues
    title: No FM5 security findings
    weight: 20
    evidence:
      type: failure-mode-clean
      target: src/
      modes: [fm5]
      max_severity: low

  - id: prompts-logged
    title: User prompt events captured in session
    weight: 10
    evidence:
      type: journey-event-present
      event: user_prompt_submit
      occurrences_min: 3

  - id: prompt-quality
    title: LLM judge: prompt quality score >= 10/20
    weight: 20
    evidence:
      type: llm-judged
      rubric: .forge/rubrics/prompt-quality.txt
      input: .forge/journey/<run-id>.jsonl
      scoring: "0-20"
      model_logical: grader

  - id: local-primitives-authored
    title: At least one L3 primitive in .forge/local/
    weight: 10
    evidence:
      type: primitive-authored
      min_count: 1

  - id: build-and-readme
    title: Build passes AND README exists
    weight: 10
    evidence:
      type: compound
      op: AND
      children:
        - type: file-exists
          path: README.md
        - type: shell
          cmd: "make build"
          expect_exit: 0
```

## When to invoke

- **`make grade`** — Makefile recipe in any lab (standard target per Spec A §13.1).
- **Post-session** — triggered by a `SessionEnd` hook or manually via `/lab-grader` slash command.
- **CI (dormant)** — `.github/workflows/grade.yml` (disabled by default; enabled per lab config).

## Adapters

- Claude Code: `adapters/claude_code/SKILL.md` + `invoke.sh`
- Copilot: `adapters/copilot/SKILL.md` + `github-bundle/skills/lab-grader/SKILL.md` + `github-bundle/prompts/lab-grader.prompt.md`
