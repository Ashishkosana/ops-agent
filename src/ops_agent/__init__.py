"""ops-agent: planner → tools → verifier → scorecard.

Public surface is small on purpose. The CLI (`ops_agent.cli`) is the entry
point. Milestone 2 ships a deterministic planner, tool loop, and fail-closed
verifier. Metrics come from local fixtures only.
"""

from ops_agent.models import AgentResult, Scorecard, Task, Verification

__version__ = "0.1.0"

__all__ = ["AgentResult", "Scorecard", "Task", "Verification", "__version__"]
