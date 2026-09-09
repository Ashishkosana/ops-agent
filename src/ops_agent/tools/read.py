"""read_file — read one workspace file. Path escape is rejected."""

from __future__ import annotations

from pathlib import Path

from ops_agent.models import ToolName, ToolResult
from ops_agent.tools._paths import resolve_inside


def read_file(workspace: Path, relative: str) -> ToolResult:
    """Return the contents of `relative` if it stays inside `workspace`."""
    root = workspace.resolve()
    if not root.is_dir():
        return ToolResult(
            name=ToolName.READ_FILE,
            ok=False,
            output=f"workspace not found: {root}",
        )
    try:
        path = resolve_inside(root, relative)
    except ValueError as exc:
        return ToolResult(name=ToolName.READ_FILE, ok=False, output=str(exc))
    if not path.is_file():
        return ToolResult(name=ToolName.READ_FILE, ok=False, output=f"not a file: {relative}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ToolResult(name=ToolName.READ_FILE, ok=False, output=f"read failed: {exc}")
    return ToolResult(
        name=ToolName.READ_FILE,
        ok=True,
        output=text,
        metadata={"path": relative, "bytes": len(text.encode("utf-8"))},
    )
