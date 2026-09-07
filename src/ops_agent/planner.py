"""Task planner.

# YOU IMPLEMENT

Ashish owns this module. The scaffold only defines the contract: a `Task` in,
a `Plan` of tool-using steps out. How you decompose (search first? tests first?
patch budget?) is the interview-defensible part — do not let a generator fill it in.
"""

from __future__ import annotations

from ops_agent.markers import YOU_IMPLEMENT_PLANNER
from ops_agent.models import Plan, Task


def plan(task: Task) -> Plan:
    """Decompose `task` into ordered steps the agent loop can execute.

    Intended (not implemented) shape:
        1. search_codebase for the failing symbol / endpoint / import
        2. run_tests to capture the current failure
        3. apply_patch with a minimal unified diff
        4. run_tests again
    """
    raise NotImplementedError(f"{YOU_IMPLEMENT_PLANNER} (task={task.id})")
