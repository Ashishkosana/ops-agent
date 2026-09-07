"""Scorecard: pass rate, cost, latency — pending until the agent exists.

Numbers here come only from local fixtures. Until `AgentResult.implemented`
is true, every metric is the literal em-dash. We never print 0.00 or a
made-up production figure.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ops_agent.eval.fixtures import Fixture
from ops_agent.markers import PENDING
from ops_agent.models import AgentResult, RunStatus, Scorecard, ScorecardRow
from ops_agent.tools.metering import summary as metering_summary


def _pending_row(task_id: str, notes: str) -> ScorecardRow:
    meter = metering_summary()
    return ScorecardRow(
        task_id=task_id,
        status=RunStatus.NOT_IMPLEMENTED,
        pass_rate=PENDING,
        cost_usd=meter["cost_usd"],
        latency_ms=meter["latency_ms"],
        notes=notes,
    )


def score_result(fixture: Fixture, result: AgentResult | None) -> ScorecardRow:
    """Score one fixture. Pending if the agent has not run for real."""
    if result is None or not result.implemented:
        return _pending_row(
            fixture.task.id,
            "agent not implemented — metrics withheld",
        )

    # Local-fixture scoring only. Cost/latency stay pending until metering exists.
    meter = metering_summary()
    tests_ok = result.tests_passed is True and fixture.labels.tests_should_pass
    expected = set(fixture.labels.expected_files_changed)
    changed = set(result.files_changed)
    files_ok = bool(expected) and expected <= changed
    passed = tests_ok and files_ok
    return ScorecardRow(
        task_id=fixture.task.id,
        status=RunStatus.PASS if passed else RunStatus.FAIL,
        pass_rate="1/1" if passed else "0/1",
        cost_usd=meter["cost_usd"],
        latency_ms=meter["latency_ms"],
        notes="scored from local fixture labels only",
    )


def build_scorecard(
    fixtures: Sequence[Fixture],
    results: Mapping[str, AgentResult] | None = None,
) -> Scorecard:
    results = results or {}
    rows = tuple(score_result(fix, results.get(fix.task.id)) for fix in fixtures)
    return Scorecard(rows=rows)


def format_scorecard(scorecard: Scorecard) -> str:
    """Human-readable table. Em-dashes are the honest unset state."""
    headers = ("fixture", "pass", "cost", "latency", "status")
    widths = [len(h) for h in headers]
    body: list[tuple[str, str, str, str, str]] = []
    for row in scorecard.rows:
        cells = (
            row.task_id,
            row.pass_rate,
            row.cost_usd,
            row.latency_ms,
            row.status.value,
        )
        body.append(cells)
        for i, cell in enumerate(cells):
            widths[i] = max(widths[i], len(cell))

    def fmt(cells: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    lines = [
        "ops-agent scorecard",
        fmt(headers),
        fmt(tuple("-" * w for w in widths)),
    ]
    lines.extend(fmt(row) for row in body)
    lines.append("")
    lines.append(scorecard.disclaimer)
    return "\n".join(lines)
