"""Typed domain models. Pure data — no I/O, no LLM calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ToolName(StrEnum):
    SEARCH_CODEBASE = "search_codebase"
    RUN_TESTS = "run_tests"
    APPLY_PATCH = "apply_patch"


class RunStatus(StrEnum):
    NOT_IMPLEMENTED = "not_implemented"
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass(frozen=True)
class Task:
    """A labeled coding/ops task loaded from an eval fixture."""

    id: str
    prompt: str
    workspace: Path
    success_criteria: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class Labels:
    """Ground truth for a fixture. Used only by the eval harness, never by tools."""

    task_id: str
    expected_files_changed: tuple[str, ...]
    tests_should_pass: bool
    gold_hint: str = ""


@dataclass(frozen=True)
class Plan:
    steps: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class ToolResult:
    name: ToolName
    ok: bool
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    """Outcome of one agent run. `implemented=False` until the loop exists."""

    task_id: str
    implemented: bool = False
    plan: Plan | None = None
    tool_calls: tuple[ToolResult, ...] = ()
    files_changed: tuple[str, ...] = ()
    tests_passed: bool | None = None
    notes: str = ""


@dataclass(frozen=True)
class Verification:
    """Verifier verdict. `implemented=False` until the policy exists."""

    implemented: bool = False
    passed: bool | None = None
    reasons: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class ScorecardRow:
    """One fixture's score. Pending metrics are the literal em-dash, never a fake 0."""

    task_id: str
    status: RunStatus
    pass_rate: str
    cost_usd: str
    latency_ms: str
    notes: str = ""


@dataclass(frozen=True)
class Scorecard:
    rows: tuple[ScorecardRow, ...]
    disclaimer: str = (
        "Honest metrics only: local fixtures/evals. No production stats. "
        "Em-dashes mean the agent has not been implemented yet."
    )
