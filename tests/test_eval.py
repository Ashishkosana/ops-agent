from __future__ import annotations

from ops_agent.eval import build_scorecard, format_scorecard, load_fixture, load_fixtures
from ops_agent.eval.__main__ import main as eval_main
from ops_agent.eval.scorecard import score_result
from ops_agent.markers import PENDING
from ops_agent.models import AgentResult, RunStatus


def test_loads_three_labeled_fixtures() -> None:
    fixtures = load_fixtures()
    ids = {fix.task.id for fix in fixtures}
    assert ids == {"fix_off_by_one", "failing_healthcheck", "broken_import"}
    for fix in fixtures:
        assert fix.task.workspace.is_dir()
        assert fix.task.prompt
        assert fix.labels.expected_files_changed
        assert fix.labels.tests_should_pass is True


def test_load_fixture_by_id() -> None:
    fixture = load_fixture("broken_import")
    assert fixture.task.id == "broken_import"
    assert (fixture.task.workspace / "helpers.py").is_file()


def test_scorecard_pending_until_agent_implemented() -> None:
    fixtures = load_fixtures()
    card = build_scorecard(fixtures)
    assert len(card.rows) == 3
    for row in card.rows:
        assert row.status is RunStatus.NOT_IMPLEMENTED
        assert row.pass_rate == PENDING
        assert row.cost_usd == PENDING
        assert row.latency_ms == PENDING
    text = format_scorecard(card)
    assert "—" in text
    assert "not_implemented" in text
    assert "local fixtures" in text.lower()
    assert "production" in text.lower()


def test_score_result_uses_labels_only_when_implemented() -> None:
    fixture = load_fixture("fix_off_by_one")
    pending = score_result(fixture, AgentResult(task_id=fixture.task.id, implemented=False))
    assert pending.pass_rate == PENDING

    done = score_result(
        fixture,
        AgentResult(
            task_id=fixture.task.id,
            implemented=True,
            files_changed=("ranges.py",),
            tests_passed=True,
        ),
    )
    assert done.status is RunStatus.PASS
    assert done.pass_rate == "1/1"
    # Cost/latency stay pending until metering exists — do not fabricate them.
    assert done.cost_usd == PENDING
    assert done.latency_ms == PENDING


def test_eval_module_main(capsys) -> None:
    assert eval_main() == 0
    out = capsys.readouterr().out
    assert "fix_off_by_one" in out
    assert "—" in out
