"""run_tests — sandbox pytest to a fixture workspace, or return a safe mock."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ops_agent.models import ToolName, ToolResult

_TIMEOUT_SECONDS = 30


def run_tests(workspace: Path, *, mock: bool = True) -> ToolResult:
    """Run pytest in `workspace`.

    Default `mock=True` does not spawn a process — CI and unit tests stay
    deterministic. Pass `mock=False` only when you intend to execute the
    fixture's own tests.
    """
    root = workspace.resolve()
    if not root.is_dir():
        return ToolResult(
            name=ToolName.RUN_TESTS,
            ok=False,
            output=f"workspace not found: {root}",
        )
    if mock:
        return ToolResult(
            name=ToolName.RUN_TESTS,
            ok=True,
            output="mock: tests not executed (safe default)",
            metadata={"mock": True, "workspace": str(root)},
        )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(root),
            "-q",
            "--tb=short",
            "--rootdir",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        cwd=root,
    )
    output = (proc.stdout + proc.stderr).strip()
    return ToolResult(
        name=ToolName.RUN_TESTS,
        ok=proc.returncode == 0,
        output=output or f"pytest exited {proc.returncode}",
        metadata={"mock": False, "returncode": proc.returncode, "workspace": str(root)},
    )
