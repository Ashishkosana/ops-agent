"""ops-agent: planner → tools → verifier → scorecard.

Public surface is small on purpose. The CLI (`ops_agent.cli`) is the entry
point. The planner, agent loop, and verifier policy are intentionally stubs —
see `YOU IMPLEMENT` markers in `planner.py`, `agent.py`, and `verifier.py`.
"""

from ops_agent.models import AgentResult, Scorecard, Task, Verification

__version__ = "0.1.0"

__all__ = ["AgentResult", "Scorecard", "Task", "Verification", "__version__"]
