"""search_codebase — read-only substring search over a fixture workspace."""

from __future__ import annotations

from pathlib import Path

from ops_agent.models import ToolName, ToolResult
from ops_agent.tools._paths import is_inside

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
_TEXT_SUFFIXES = {".py", ".txt", ".md", ".json", ".toml", ".yml", ".yaml", ".sh", ""}


def search_codebase(workspace: Path, query: str) -> ToolResult:
    """Return files/lines in `workspace` that contain `query` (case-insensitive)."""
    root = workspace.resolve()
    if not root.is_dir():
        return ToolResult(
            name=ToolName.SEARCH_CODEBASE,
            ok=False,
            output=f"workspace not found: {root}",
        )
    needle = query.lower().strip()
    if not needle:
        return ToolResult(name=ToolName.SEARCH_CODEBASE, ok=False, output="empty query")

    hits: list[str] = []
    files_matched: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not is_inside(root, path):
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES and path.suffix != "":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(root))
        matched_file = False
        for lineno, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                hits.append(f"{rel}:{lineno}:{line.rstrip()}")
                matched_file = True
        if matched_file:
            files_matched.append(rel)

    output = "\n".join(hits) if hits else f"no matches for {query!r}"
    return ToolResult(
        name=ToolName.SEARCH_CODEBASE,
        ok=True,
        output=output,
        metadata={"query": query, "files": files_matched, "hit_count": len(hits)},
    )
