"""Verifier policy.

# YOU IMPLEMENT

review-lens verifies *findings* by arguing against them. ops-agent verifies a
*run*: did tests pass, did the patch stay inside the workspace, does the
outcome match labels? The policy (strict AND of checks vs scored rubric,
whether gold hints are visible to the agent, fail-closed on missing evidence)
is Ashish's to own and defend.
"""

from __future__ import annotations

from ops_agent.markers import YOU_IMPLEMENT_VERIFIER
from ops_agent.models import AgentResult, Labels, Task, Verification


def verify(
    task: Task,
    result: AgentResult,
    labels: Labels | None = None,
) -> Verification:
    """Accept or reject `result` for `task`.

    Labels are eval-only. A production-shaped policy should be able to verify
    from `result` + workspace evidence without reading `labels`.
    """
    _ = (result, labels)
    raise NotImplementedError(f"{YOU_IMPLEMENT_VERIFIER} (task={task.id})")
