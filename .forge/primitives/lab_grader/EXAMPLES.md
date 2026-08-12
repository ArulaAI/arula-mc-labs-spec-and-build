# U2 `/lab-grader` — Usage Examples

Five real-world patterns for invoking the lab grader in development, CI, and
integration contexts. All examples assume the lab root contains `.forge/grader.yaml`.

---

## 1. Run the grader directly from a lab repo

```bash
# From the lab root — grade this session using a fresh run ID
python -m primitives.lab_grader.shared.grader . --run-id $(uuidgen) --format both
```

Sample output:

```json
{
  "run_id": "A3F21B9C-8D4E-4C6A-B7F5-2E1D9A0C3F7B",
  "total_score": 72.5,
  "max_score": 100,
  "percentage": 72.5,
  "criteria": [
    {
      "id": "build-passes",
      "passed": true,
      "score": 1.0,
      "note": "exit code 0"
    },
    {
      "id": "readme-exists",
      "passed": true,
      "score": 1.0,
      "note": "file present"
    },
    {
      "id": "prompt-quality",
      "passed": false,
      "score": 0.45,
      "note": "LLM score 9/20 (45%)"
    }
  ]
}
```

The grade report markdown section is also printed to stdout when `--format both`
is used:

```
# Grade Report — my-lab

**Run ID:** `A3F21B9C-8D4E-4C6A-B7F5-2E1D9A0C3F7B`
**Score:** 72.5% (72.5 / 100.0)

## Criteria

| ID            | Passed | Score | Note              |
|---------------|--------|-------|-------------------|
| build-passes  | ✓      | 1.00  | exit code 0       |
| readme-exists | ✓      | 1.00  | file present      |
| prompt-quality| ✗      | 0.45  | LLM score 9/20 (45%) |
```

Artifacts written after a successful run:

```
.forge/journey/<run-id>/grade.json          ← full GradeResult
.forge/journey/<run-id>.jsonl               ← lab_grader_run event appended
```

---

## 2. `grade.json` structure

The file written to `.forge/journey/<run-id>/grade.json` after each grading run:

```json
{
  "run_id": "run_abc123def456",
  "total_score": 72.5,
  "max_score": 100,
  "percentage": 72.5,
  "criteria": [
    {
      "id": "build-passes",
      "passed": true,
      "score": 1.0,
      "note": "exit code 0"
    },
    {
      "id": "readme-exists",
      "passed": true,
      "score": 1.0,
      "note": "file present"
    },
    {
      "id": "prompt-quality",
      "passed": false,
      "score": 0.45,
      "note": "LLM score 9/20 (45%)"
    }
  ]
}
```

Key fields:

| Field         | Type    | Description                                         |
|---------------|---------|-----------------------------------------------------|
| `run_id`      | string  | Session run ID passed to `grade()` or the CLI       |
| `total_score` | number  | Weighted sum of `weight × criterion_score`          |
| `max_score`   | number  | Sum of all criterion weights                        |
| `percentage`  | number  | `total_score / max_score × 100` (0–100 scale)       |
| `criteria`    | array   | Per-criterion outcome: `id`, `passed`, `score`, `note` |

---

## 3. `make grade` target in a lab Makefile

Add to any lab's `Makefile` so that `make grade` runs the grader in one step:

```makefile
# Makefile (lab root)
# ─────────────────────────────────────────
# Standard U2 target per Forge Spec A §13.1
# ─────────────────────────────────────────
PRIMITIVES_ROOT ?= ~/projects/forge-prowess-primitives
PYTHON          ?= python3
RUN_ID          ?= $(shell uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

.PHONY: grade
grade:
	FORGE_LLM_BACKEND=bedrock \
	  $(PYTHON) -m primitives.lab_grader.shared.grader . \
	    --run-id $(RUN_ID) \
	    --format both

.PHONY: grade-dry
grade-dry:
	FORGE_LLM_BACKEND=mock \
	  $(PYTHON) -m primitives.lab_grader.shared.grader . \
	    --run-id dry-$(RUN_ID) \
	    --format json
```

Usage:

```bash
# Grade with real LLM backend (Bedrock via llm-proxy)
make grade

# Grade with mock backend for offline dry-runs
make grade-dry
```

---

## 4. Pre-commit hook integration

Wire the grader into `pre-commit` so every `git commit` produces a grade artifact.
Add to `.pre-commit-config.yaml` in the lab repo:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: forge-grade
        name: Forge lab grader
        language: python
        entry: python -m primitives.lab_grader.shared.grader
        args:
          - "."
          - "--format"
          - "json"
        # Run only when forge rubric or source files change
        files: '(\.forge/grader\.yaml|src/|tests/)'
        pass_filenames: false
        additional_dependencies: []
```

The hook runs silently and writes `grade.json` to `.forge/journey/`. Because
`entry` uses `python -m`, the grader exits 0 on any completed grading run
(even a low score). To block commits on failing scores, set exit-code handling
in a wrapper script:

```bash
#!/usr/bin/env bash
# .forge/hooks/pre-commit-grade.sh
set -euo pipefail
RUN_ID="pre-commit-$(git rev-parse --short HEAD)"
python -m primitives.lab_grader.shared.grader . --run-id "$RUN_ID" --format json
SCORE=$(jq '.percentage' ".forge/journey/${RUN_ID}/grade.json")
if (( $(echo "$SCORE < 50" | bc -l) )); then
  echo "❌ Lab score ${SCORE}% is below 50% threshold. Commit blocked." >&2
  exit 1
fi
```

---

## 5. Project 1 sim-content-snapshot integration

The Forge Prowess showcase calls the grader after a sim session completes. The
`services/sim-content` service reads the S3 snapshot, then `services/playground`
invokes the grader via the `grade()` Python API (not the CLI) so the grade
result can be stored in DynamoDB and forwarded to the telemetry pipeline.

```python
# services/playground/grading.py (abbreviated)
import uuid
from pathlib import Path
from primitives.lab_grader.shared.grader import grade, GradeResult
from primitives._llm import BedrockBackend

def run_grade_for_session(
    lab_snapshot_dir: Path,
    session_run_id: str,
) -> GradeResult:
    """Grade a completed sim session and return the GradeResult.

    Args:
        lab_snapshot_dir: Local path where the S3 lab snapshot was extracted.
        session_run_id:   The run ID that identifies the sim session; used to
                          locate the session JSONL and name all grade artifacts.

    Returns:
        GradeResult with total_score, percentage, and per-criterion outcomes.
    """
    backend = BedrockBackend()  # routes through services/llm-proxy
    result: GradeResult = grade(
        lab_root=lab_snapshot_dir,
        run_id=session_run_id,
        llm_backend=backend,
    )
    return result

# Caller in the sim completion handler:
snapshot_dir = Path("/tmp/sim-snapshots") / invitee_id / session_id
result = run_grade_for_session(snapshot_dir, session_run_id=session_id)

# Store in DynamoDB for the showcase scorecard
store_grade_result(
    invitee_id=invitee_id,
    session_id=session_id,
    percentage=result.percentage,
    criteria=[
        {"id": cid, "passed": ev.passed, "score": ev.score}
        for cid, ev in result.criteria_results
    ],
)
```

The `grade.json` artifact is also uploaded to S3 alongside the session JSONL so
the admin console can surface per-criterion breakdowns for Arula reviewers.
