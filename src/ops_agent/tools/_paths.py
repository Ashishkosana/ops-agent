"""Path containment helpers. Tools must not touch files outside a workspace."""

from __future__ import annotations

from pathlib import Path


def resolve_inside(workspace: Path, relative: str) -> Path:
    """Resolve `relative` under `workspace` or raise ValueError."""
    root = workspace.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes workspace: {relative}")
    return candidate


def is_inside(workspace: Path, path: Path) -> bool:
    root = workspace.resolve()
    candidate = path.resolve()
    return candidate == root or root in candidate.parents
