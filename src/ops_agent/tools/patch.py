"""apply_patch — safe dry-run mock. Real writes are a later stub."""

from __future__ import annotations

import re
from pathlib import Path

from ops_agent.markers import LATER_STUB_PATCH
from ops_agent.models import ToolName, ToolResult
from ops_agent.tools._paths import resolve_inside

_DIFF_FILE = re.compile(r"^(?:---|\+\+\+) [ab]/(.+)$", re.MULTILINE)


def apply_patch(workspace: Path, diff: str, *, dry_run: bool = True) -> ToolResult:
    """Record a unified diff against `workspace` without writing files.

    Rejects paths that escape the workspace. `dry_run=False` is not
    implemented — that is the later stub for real application.
    """
    root = workspace.resolve()
    if not root.is_dir():
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output=f"workspace not found: {root}",
        )
    if not dry_run:
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output=LATER_STUB_PATCH,
            metadata={"dry_run": False},
        )

    paths: list[str] = []
    try:
        for match in _DIFF_FILE.finditer(diff):
            rel = match.group(1).strip()
            resolve_inside(root, rel)
            if rel not in paths:
                paths.append(rel)
    except ValueError as exc:
        return ToolResult(name=ToolName.APPLY_PATCH, ok=False, output=str(exc))

    if not paths and diff.strip():
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output="not a unified diff (expected --- a/ and +++ b/ headers)",
        )

    return ToolResult(
        name=ToolName.APPLY_PATCH,
        ok=True,
        output=f"dry-run: would patch {', '.join(paths) or '(no files)'}",
        metadata={"dry_run": True, "files": paths, "wrote": False},
    )


def apply_patch_for_real(workspace: Path, diff: str) -> ToolResult:
    """LATER STUB: write a validated unified diff inside `workspace`."""
    return apply_patch(workspace, diff, dry_run=False)
