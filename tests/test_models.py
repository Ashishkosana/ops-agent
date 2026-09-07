from __future__ import annotations

from pathlib import Path

from ops_agent.markers import PENDING
from ops_agent.models import AgentResult, RunStatus, ScorecardRow, Task, ToolName


def test_task_is_frozen(tmp_path: Path) -> None:
    task = Task(id="t", prompt="p", workspace=tmp_path)
    assert task.id == "t"
    assert task.success_criteria == ()


def test_agent_result_defaults_unimplemented() -> None:
    result = AgentResult(task_id="t")
    assert result.implemented is False
    assert result.tests_passed is None
    assert result.tool_calls == ()


def test_tool_name_values() -> None:
    assert ToolName.SEARCH_CODEBASE == "search_codebase"
    assert ToolName.RUN_TESTS == "run_tests"
    assert ToolName.APPLY_PATCH == "apply_patch"


def test_pending_row_uses_emdash_not_zero() -> None:
    row = ScorecardRow(
        task_id="t",
        status=RunStatus.NOT_IMPLEMENTED,
        pass_rate=PENDING,
        cost_usd=PENDING,
        latency_ms=PENDING,
    )
    assert row.pass_rate == "—"
    assert row.cost_usd != "0"
    assert row.latency_ms != "0"
