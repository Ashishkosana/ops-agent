"""Cost and latency metering for a single local run.

Numbers come from `record_usage` on this process — wall-clock latency and
token counts the caller actually observed. There is no production traffic
and no invented bill. Deterministic (no-LLM) runs record $0.0000.
"""

from __future__ import annotations

from dataclasses import dataclass

from ops_agent.markers import PENDING


@dataclass
class _State:
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    recorded: bool = False


_state = _State()


def reset() -> None:
    """Clear the in-process meter. Call at the start of each agent run."""
    _state.tokens_in = 0
    _state.tokens_out = 0
    _state.latency_ms = 0
    _state.recorded = False


def record_usage(*, tokens_in: int = 0, tokens_out: int = 0, latency_ms: int = 0) -> None:
    """Accumulate one measured span. Do not call this with guessed numbers."""
    _state.tokens_in += tokens_in
    _state.tokens_out += tokens_out
    _state.latency_ms += latency_ms
    _state.recorded = True


def summary() -> dict[str, str]:
    """Return measured figures, or em-dashes if nothing was recorded."""
    if not _state.recorded:
        return {"cost_usd": PENDING, "latency_ms": PENDING, "tokens": PENDING}
    # No model in the default planner — cost is honestly zero, not "unknown".
    cost = 0.0
    return {
        "cost_usd": f"{cost:.4f}",
        "latency_ms": str(_state.latency_ms),
        "tokens": str(_state.tokens_in + _state.tokens_out),
    }
