"""Agent loop: planner → tools → verifier.

# YOU IMPLEMENT

This is the core. The scaffold refuses to invent a loop, a retry policy, or a
stop condition. Ashish owns those decisions and should be able to defend them
against: infinite tool use, patching outside the workspace, and "tests passed
because we never ran them."
"""

from __future__ import annotations

from ops_agent.markers import YOU_IMPLEMENT_AGENT
from ops_agent.models import AgentResult, Task
from ops_agent.tools.base import Toolbelt


def run(task: Task, tools: Toolbelt | None = None) -> AgentResult:
    """Execute one task end-to-end.

    Intended (not implemented) shape::

        plan = planner.plan(task)
        for step in plan.steps:
            # dispatch search_codebase / run_tests / apply_patch via `tools`
            ...
        verdict = verifier.verify(task, result)
        return result
    """
    _ = tools  # reserved for the real loop
    raise NotImplementedError(f"{YOU_IMPLEMENT_AGENT} (task={task.id})")
