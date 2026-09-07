"""Cost and latency metering.

# LATER STUB

Do not invent token counts, dollar costs, or latencies. When this is
implemented, numbers must come from measured tool/LLM usage on local
fixture runs — never from hardcoded "production" stats.
"""

from __future__ import annotations

from ops_agent.markers import LATER_STUB_METERING, PENDING


def record_usage(*, tokens_in: int = 0, tokens_out: int = 0, latency_ms: int = 0) -> None:
    """Record one model or tool span. Not implemented."""
    _ = (tokens_in, tokens_out, latency_ms)
    raise NotImplementedError(LATER_STUB_METERING)


def summary() -> dict[str, str]:
    """Return pending placeholders until metering exists."""
    return {"cost_usd": PENDING, "latency_ms": PENDING, "tokens": PENDING}
