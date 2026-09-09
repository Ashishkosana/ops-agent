"""Planner → tools → verifier against labeled fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ops_agent.agent import run as run_agent
from ops_agent.eval.fixtures import load_fixture, load_fixtures
from ops_agent.models import AgentResult, ToolName, ToolResult
from ops_agent.planner import PLANNER_MODE_ENV, extract_search_queries, plan
from ops_agent.tools.base import Toolbelt
from ops_agent.verifier import verify


def test_planner_is_deterministic_and_finite() -> None:
    fixture = load_fixture("fix_off_by_one")
    planned = plan(fixture.task)
    assert planned.steps
    assert any(step.startswith("search_codebase") for step in planned.steps)
    assert planned.steps.count("run_tests") == 2
    assert "apply_patch" in planned.steps
    assert "llm" not in planned.notes.lower() or "no llm" in planned.notes.lower()


def test_planner_extracts_prompt_needles_not_gold_hints() -> None:
    queries = extract_search_queries(
        "inclusive_upto(n) should return 0..n. The probe still calls /status."
    )
    assert "inclusive_upto" in queries
    assert "/status" in queries


def test_llm_planner_requires_key_and_stays_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = load_fixture("fix_off_by_one")
    monkeypatch.setenv(PLANNER_MODE_ENV, "llm")
    monkeypatch.delenv("OPS_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPS_AGENT_API_KEY"):
        plan(fixture.task)
    monkeypatch.setenv("OPS_AGENT_API_KEY", "sk-not-a-real-key")
    with pytest.raises(RuntimeError, match="no vendor client"):
        plan(fixture.task)


@pytest.mark.parametrize("fixture_id", ["fix_off_by_one", "broken_import", "failing_healthcheck"])
def test_agent_solves_labeled_fixture(fixture_id: str) -> None:
    fixture = load_fixture(fixture_id)
    before = {
        path: path.read_text(encoding="utf-8")
        for path in fixture.task.workspace.rglob("*.py")
    }
    result = run_agent(fixture.task)
    assert result.implemented is True
    assert result.tests_passed is True
    assert set(fixture.labels.expected_files_changed) <= set(result.files_changed)
    assert result.verification is not None
    assert result.verification.passed is True
    assert result.cost_usd == 0.0
    assert result.latency_ms is not None
    assert result.latency_ms >= 0
    for path, text in before.items():
        assert path.read_text(encoding="utf-8") == text


def test_agent_modules_do_not_read_gold_hints() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "ops_agent"
    for name in ("agent.py", "planner.py", "repair.py"):
        text = (root / name).read_text(encoding="utf-8")
        assert "gold_hint" not in text
        assert "labels.json" not in text


def test_verifier_fail_closed_without_real_tests() -> None:
    fixture = load_fixture("fix_off_by_one")
    unimplemented = verify(fixture.task, AgentResult(task_id=fixture.task.id), fixture.labels)
    assert unimplemented.passed is False

    mocked = AgentResult(
        task_id=fixture.task.id,
        implemented=True,
        files_changed=("ranges.py",),
        tests_passed=True,
        tool_calls=(
            ToolResult(
                name=ToolName.RUN_TESTS,
                ok=True,
                output="mock: tests not executed (safe default)",
                metadata={"mock": True},
            ),
        ),
    )
    verdict = verify(fixture.task, mocked, labels=None)
    assert verdict.implemented is True
    assert verdict.passed is False
    assert any("mock" in reason for reason in verdict.reasons)


def test_verifier_rejects_missing_files_when_labeled() -> None:
    fixture = load_fixture("fix_off_by_one")
    result = AgentResult(
        task_id=fixture.task.id,
        implemented=True,
        files_changed=(),
        tests_passed=True,
        tool_calls=(
            ToolResult(
                name=ToolName.RUN_TESTS,
                ok=True,
                output="ok",
                metadata={"mock": False},
            ),
        ),
    )
    verdict = verify(fixture.task, result, fixture.labels)
    assert verdict.passed is False
    assert any("files" in reason for reason in verdict.reasons)


def test_safe_toolbelt_does_not_write_or_pass_verifier() -> None:
    fixture = load_fixture("fix_off_by_one")
    belt = Toolbelt(workspace=fixture.task.workspace, safe_mocks=True)
    result = run_agent(fixture.task, tools=belt)
    assert result.implemented is True
    assert result.verification is not None
    assert result.verification.passed is False
    assert "range(n)" in (fixture.task.workspace / "ranges.py").read_text(encoding="utf-8")


def test_eval_fixtures_still_three() -> None:
    assert len(load_fixtures()) == 3
