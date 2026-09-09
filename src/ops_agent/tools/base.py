"""Toolbelt: the tools the agent is allowed to call.

Safe by default: search/read stay inside the workspace, tests do not shell
out, patches are dry-run. Pass `safe_mocks=False` only when the agent should
execute pytest and write a validated diff (eval / `ops-agent run --agent`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ops_agent.models import ToolResult
from ops_agent.tools.patch import apply_patch
from ops_agent.tools.read import read_file
from ops_agent.tools.search import search_codebase
from ops_agent.tools.tests import run_tests


@dataclass(frozen=True)
class Toolbelt:
    """Bound tool set for one workspace.

    `safe_mocks=True` (default) never writes files and never shells out.
    That is what unit tests use unless they opt into a real run.
    """

    workspace: Path
    safe_mocks: bool = True

    def search_codebase(self, query: str) -> ToolResult:
        return search_codebase(self.workspace, query)

    def read_file(self, relative: str) -> ToolResult:
        return read_file(self.workspace, relative)

    def run_tests(self) -> ToolResult:
        return run_tests(self.workspace, mock=self.safe_mocks)

    def apply_patch(self, diff: str) -> ToolResult:
        return apply_patch(self.workspace, diff, dry_run=self.safe_mocks)
