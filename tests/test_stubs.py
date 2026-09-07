"""Stubs must fail closed with YOU IMPLEMENT — never silently succeed."""

from __future__ import annotations

import pytest

from ops_agent.agent import run as run_agent
from ops_agent.eval.fixtures import load_fixture
from ops_agent.markers import (
    LATER_STUB_METERING,
    YOU_IMPLEMENT_AGENT,
    YOU_IMPLEMENT_PLANNER,
    YOU_IMPLEMENT_VERIFIER,
)
from ops_agent.models import AgentResult
from ops_agent.planner import plan
from ops_agent.tools.metering import record_usage
from ops_agent.verifier import verify


@pytest.fixture
def fixture():
    return load_fixture("fix_off_by_one")


def test_planner_is_you_implement(fixture) -> None:
    with pytest.raises(NotImplementedError, match="YOU IMPLEMENT") as exc:
        plan(fixture.task)
    assert YOU_IMPLEMENT_PLANNER in str(exc.value)


def test_agent_is_you_implement(fixture) -> None:
    with pytest.raises(NotImplementedError, match="YOU IMPLEMENT") as exc:
        run_agent(fixture.task)
    assert YOU_IMPLEMENT_AGENT in str(exc.value)


def test_verifier_is_you_implement(fixture) -> None:
    result = AgentResult(task_id=fixture.task.id)
    with pytest.raises(NotImplementedError, match="YOU IMPLEMENT") as exc:
        verify(fixture.task, result, fixture.labels)
    assert YOU_IMPLEMENT_VERIFIER in str(exc.value)


def test_metering_is_later_stub() -> None:
    with pytest.raises(NotImplementedError, match="LATER STUB") as exc:
        record_usage(tokens_in=1)
    assert LATER_STUB_METERING in str(exc.value)
