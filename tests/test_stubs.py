"""Ownership markers stay visible; metering is measured, not invented."""

from __future__ import annotations

from ops_agent.markers import (
    LATER_STUB_MARKETPLACE,
    YOU_IMPLEMENT_AGENT,
    YOU_IMPLEMENT_PLANNER,
    YOU_IMPLEMENT_VERIFIER,
)
from ops_agent.tools.metering import record_usage, reset, summary


def test_ownership_markers_still_name_the_core() -> None:
    assert "planner" in YOU_IMPLEMENT_PLANNER.lower()
    assert "agent loop" in YOU_IMPLEMENT_AGENT.lower()
    assert "verifier" in YOU_IMPLEMENT_VERIFIER.lower()
    assert "marketplace" in LATER_STUB_MARKETPLACE.lower()


def test_metering_pending_until_recorded() -> None:
    reset()
    pending = summary()
    assert pending["cost_usd"] == "—"
    assert pending["latency_ms"] == "—"


def test_metering_records_measured_local_usage() -> None:
    reset()
    record_usage(tokens_in=0, tokens_out=0, latency_ms=12)
    measured = summary()
    assert measured["latency_ms"] == "12"
    assert measured["cost_usd"] == "0.0000"
    assert measured["tokens"] == "0"
    reset()
