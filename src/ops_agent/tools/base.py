"""Toolbelt: the three tools the agent is allowed to call.

Safe by default: search is read-only, tests stay inside the workspace,
patches are recorded and not written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ops_agent.models import ToolResult
from ops_agent.tools.patch import apply_patch
from ops_agent.tools.search import search_codebase
from ops_agent.tools.tests import run_tests


@dataclass(frozen=True)
class Toolbelt:
    """Bound tool set for one workspace.

    `safe_mocks=True` (default) never writes files and never shells out.
    That is what CI and unit tests use.
    """

    workspace: Path
    safe_mocks: bool = True

    def search_codebase(self, query: str) -> ToolResult:
        return search_codebase(self.workspace, query)

    def run_tests(self) -> ToolResult:
        return run_tests(self.workspace, mock=self.safe_mocks)

    def apply_patch(self, diff: str) -> ToolResult:
        return apply_patch(self.workspace, diff, dry_run=True)
