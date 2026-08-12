"""Rubric DSL parser — Pydantic v2 discriminated-union models.

Parses `.forge/grader.yaml` files into a validated `Rubric` object.
All 7 evidence types are represented as Pydantic models keyed on the
`type` discriminator field.

Raises:
    RubricViolation: for any semantic or structural error in the rubric.
    yaml.YAMLError:  for syntactically broken YAML (propagated as-is).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RubricViolation(Exception):
    """Raised when a rubric file is missing, malformed, or semantically invalid."""


# ---------------------------------------------------------------------------
# Evidence models — one per type, discriminated on the `type` field
# ---------------------------------------------------------------------------


class ShellEvidence(BaseModel):
    type: Literal["shell"]
    cmd: str
    expect_exit: int = 0
    timeout: int = 120


class FileExistsEvidence(BaseModel):
    type: Literal["file-exists"]
    path: str
    min_length: int = 0


class FailureModeCleanEvidence(BaseModel):
    type: Literal["failure-mode-clean"]
    target: str = "."
    modes: list[str] | None = None
    max_severity: Literal["low", "medium", "high", "critical"] = "low"


class JourneyEventPresentEvidence(BaseModel):
    type: Literal["journey-event-present"]
    event: str
    occurrences_min: int = 1
    where: str | None = None
    before: str | None = None


class LlmJudgedEvidence(BaseModel):
    type: Literal["llm-judged"]
    rubric: str
    input: str
    scoring: str  # e.g. "0-20"
    model_logical: str = "grader"


class PrimitiveAuthoredEvidence(BaseModel):
    type: Literal["primitive-authored"]
    min_count: int = 1
    primitive_name: str | None = None
    primitive_kind: str | None = None


class CompoundEvidence(BaseModel):
    type: Literal["compound"]
    op: Literal["AND", "OR"]
    children: list[EvidenceUnion]

    @model_validator(mode="after")
    def _children_not_empty(self) -> CompoundEvidence:
        if not self.children:
            raise ValueError("CompoundEvidence.children must not be empty")
        return self


# Forward reference resolution — CompoundEvidence.children uses EvidenceUnion
EvidenceUnion = Annotated[
    ShellEvidence
    | FileExistsEvidence
    | FailureModeCleanEvidence
    | JourneyEventPresentEvidence
    | LlmJudgedEvidence
    | PrimitiveAuthoredEvidence
    | CompoundEvidence,
    Field(discriminator="type"),
]

CompoundEvidence.model_rebuild()


# ---------------------------------------------------------------------------
# Criterion + Rubric root models
# ---------------------------------------------------------------------------


class Criterion(BaseModel):
    id: str
    title: str
    weight: int
    evidence: EvidenceUnion

    @field_validator("weight", mode="before")
    @classmethod
    def _coerce_weight(cls, v: int | float | str) -> int:
        return int(v)


class Rubric(BaseModel):
    lab: str
    forge_primitives_version: str
    total_points: int
    criteria: list[Criterion]

    @field_validator("total_points", mode="before")
    @classmethod
    def _coerce_total(cls, v: int | float | str) -> int:
        return int(v)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_rubric(path: Path) -> Rubric:
    """Load and validate a grader.yaml file.

    Args:
        path: Absolute or relative path to the grader.yaml file.

    Returns:
        A validated :class:`Rubric` instance.

    Raises:
        RubricViolation: If the file is missing or semantically invalid.
        yaml.YAMLError:  If the file is syntactically broken YAML.
    """
    if not path.exists():
        raise RubricViolation(f"Rubric file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise RubricViolation(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise RubricViolation(f"Rubric must be a YAML mapping, got {type(raw).__name__}: {path}")

    try:
        return Rubric.model_validate(raw)
    except Exception as exc:  # pydantic.ValidationError
        raise RubricViolation(f"Rubric validation error in {path}: {exc}") from exc
