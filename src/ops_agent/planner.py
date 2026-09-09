"""Task planner.

Deterministic by default so CI needs no API key. An LLM path exists only as
a gated stub: set OPS_AGENT_PLANNER=llm *and* OPS_AGENT_API_KEY (or
OPENAI_API_KEY). That path refuses rather than calling a vendor — this
package ships no client and CI stays offline.

The plan is a finite strategy, not an open-ended chat: search what the
prompt names, run tests for evidence, apply one hypothesized patch, re-test.
The agent loop may read files the search surfaced; it does not invent extra
unbounded steps.
"""

from __future__ import annotations

import os
import re

from ops_agent.models import Plan, Task

PLANNER_MODE_ENV = "OPS_AGENT_PLANNER"
_LLM_MODES = frozenset({"llm", "openai"})

# Words that show up in every fixture prompt and are useless as search keys.
_STOP = frozenset(
    {
        "should",
        "return",
        "tests",
        "fail",
        "find",
        "the",
        "and",
        "patch",
        "from",
        "import",
        "wrong",
        "search",
        "then",
        "with",
        "but",
        "for",
        "this",
        "that",
        "still",
        "calls",
        "fix",
        "probe",
        "service",
        "exposes",
        "script",
        "failing",
        "not",
        "does",
        "exist",
    }
)


def plan(task: Task) -> Plan:
    """Decompose `task` into ordered tool steps."""
    mode = os.environ.get(PLANNER_MODE_ENV, "deterministic").strip().lower()
    if mode in _LLM_MODES:
        return _llm_plan(task)
    return _deterministic_plan(task)


def extract_search_queries(prompt: str) -> tuple[str, ...]:
    """Pull search needles from a task prompt. No labels, no gold hints."""
    found: list[str] = []

    def add(item: str) -> None:
        text = item.strip()
        if text and text.lower() not in _STOP and text not in found:
            found.append(text)

    for match in re.finditer(r"'([^']+)'|\"([^\"]+)\"", prompt):
        quoted = match.group(1) or match.group(2)
        add(quoted)
        for part in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", quoted):
            add(part)
    for match in re.findall(r"/[A-Za-z][\w\-]*", prompt):
        add(match)
    for match in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\s*\(", prompt):
        add(match.rstrip(" (").strip())
    for match in re.findall(r"\b[a-z_][a-z0-9_]+\.[a-z_][a-z0-9_]+", prompt):
        add(match.split(".")[-1])
    return tuple(found)


def _deterministic_plan(task: Task) -> Plan:
    queries = extract_search_queries(task.prompt)
    steps: list[str] = []
    if queries:
        for query in queries[:3]:
            steps.append(f"search_codebase: {query}")
    else:
        steps.append("search_codebase: def")
    # Search orients. Tests are the spec. One patch, then a confirming run.
    # Finite plan = stop condition. We do not loop until green.
    steps.extend(["run_tests", "apply_patch", "run_tests"])
    return Plan(
        steps=tuple(steps),
        notes="deterministic search → test → patch → re-test (no LLM)",
    )


def _llm_plan(task: Task) -> Plan:
    """Gated placeholder. Never calls a network from CI."""
    _ = task
    key = os.environ.get("OPS_AGENT_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPS_AGENT_PLANNER=llm requires OPS_AGENT_API_KEY or OPENAI_API_KEY. "
            "Unset OPS_AGENT_PLANNER to use the deterministic planner."
        )
    raise RuntimeError(
        "LLM planner is gated and this package ships no vendor client. "
        "Unset OPS_AGENT_PLANNER for the offline deterministic planner."
    )
