"""Verifier policy.

review-lens verifies *findings*. This verifies a *run*: did we actually
execute tests, did a patch stay inside the workspace, is there evidence
rather than a mock green?

Policy (fail-closed, all must hold):

1. The loop ran (`result.implemented`).
2. Tests were executed for real (last `run_tests` is not a mock) and passed.
3. At least one file changed.
4. No tool reported a path escape.
5. If eval labels are supplied: expected files ⊆ changed, and
   `tests_should_pass` matches. `gold_hint` is never a pass condition —
   a hint is not evidence.

A production-shaped call (`labels=None`) still requires 1-4. Missing
evidence is a reject, not a skip.
"""

from __future__ import annotations

from ops_agent.models import AgentResult, Labels, Task, ToolName, Verification


def verify(
    task: Task,
    result: AgentResult,
    labels: Labels | None = None,
) -> Verification:
    """Accept or reject `result` for `task`."""
    _ = task
    reasons: list[str] = []

    if not result.implemented:
        return Verification(
            implemented=True,
            passed=False,
            reasons=("agent loop did not run",),
            notes="fail-closed: unimplemented result",
        )

    if _path_escape(result):
        reasons.append("a tool reported a path that escaped the workspace")

    if not result.files_changed:
        reasons.append("no files changed")

    if not _real_tests_ran(result):
        reasons.append("tests were not executed (missing run_tests or last run was a mock)")
    elif result.tests_passed is not True:
        reasons.append("workspace tests did not pass")

    if labels is not None:
        expected = set(labels.expected_files_changed)
        changed = set(result.files_changed)
        missing = expected - changed
        if expected and missing:
            reasons.append(f"expected files not patched: {', '.join(sorted(missing))}")
        if labels.tests_should_pass and result.tests_passed is not True:
            reasons.append("labels require tests to pass")
        # gold_hint is intentionally unused.

    passed = not reasons
    if passed:
        reasons.append("tests passed on a real run; patch stayed in-workspace")
    return Verification(
        implemented=True,
        passed=passed,
        reasons=tuple(reasons),
        notes="fail-closed policy; labels optional; gold hints unused",
    )


def _real_tests_ran(result: AgentResult) -> bool:
    runs = [call for call in result.tool_calls if call.name is ToolName.RUN_TESTS]
    if not runs:
        return False
    return runs[-1].metadata.get("mock") is False


def _path_escape(result: AgentResult) -> bool:
    return any("escapes workspace" in call.output for call in result.tool_calls)
