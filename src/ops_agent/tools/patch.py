"""apply_patch — validate a unified diff, optionally write inside the workspace."""

from __future__ import annotations

import re
from pathlib import Path

from ops_agent.models import ToolName, ToolResult
from ops_agent.tools._paths import resolve_inside

_DIFF_FILE = re.compile(r"^(?:---|\+\+\+) [ab]/(.+)$", re.MULTILINE)
_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_patch(workspace: Path, diff: str, *, dry_run: bool = True) -> ToolResult:
    """Apply a unified diff against `workspace`.

    Paths that escape the workspace are rejected. `dry_run=True` (the Toolbelt
    safe default) records files only. `dry_run=False` writes after the same
    containment checks — still fail-closed on a hunk that does not match.
    """
    root = workspace.resolve()
    if not root.is_dir():
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output=f"workspace not found: {root}",
        )

    try:
        paths = _diff_paths(root, diff)
    except ValueError as exc:
        return ToolResult(name=ToolName.APPLY_PATCH, ok=False, output=str(exc))

    if not paths and diff.strip():
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output="not a unified diff (expected --- a/ and +++ b/ headers)",
        )

    if dry_run:
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=True,
            output=f"dry-run: would patch {', '.join(paths) or '(no files)'}",
            metadata={"dry_run": True, "files": paths, "wrote": False},
        )

    try:
        written = _apply_unified_diff(root, diff)
    except ValueError as exc:
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output=str(exc),
            metadata={"dry_run": False, "files": paths, "wrote": False},
        )

    return ToolResult(
        name=ToolName.APPLY_PATCH,
        ok=True,
        output=f"wrote {', '.join(written) or '(no files)'}",
        metadata={"dry_run": False, "files": written, "wrote": True},
    )


def apply_patch_for_real(workspace: Path, diff: str) -> ToolResult:
    """Write a validated unified diff inside `workspace`."""
    return apply_patch(workspace, diff, dry_run=False)


def _diff_paths(root: Path, diff: str) -> list[str]:
    paths: list[str] = []
    for match in _DIFF_FILE.finditer(diff):
        rel = match.group(1).strip()
        resolve_inside(root, rel)
        if rel not in paths:
            paths.append(rel)
    return paths


def _apply_unified_diff(root: Path, diff: str) -> list[str]:
    """Apply hunks. Raises ValueError if a file escapes or a hunk mismatches."""
    written: list[str] = []
    for rel, file_diff in _split_file_diffs(diff):
        dest = resolve_inside(root, rel)
        original = dest.read_text(encoding="utf-8") if dest.is_file() else ""
        updated = _apply_hunks(original, file_diff, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(updated, encoding="utf-8")
        if rel not in written:
            written.append(rel)
    return written


def _split_file_diffs(diff: str) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current_rel: str | None = None
    current_lines: list[str] = []
    plus_rel: str | None = None
    for raw in diff.splitlines():
        if raw.startswith("--- "):
            if current_rel is not None and current_lines:
                blocks.append((plus_rel or current_rel, current_lines))
            current_rel = _strip_ab_prefix(raw[4:].strip().split("\t", 1)[0])
            plus_rel = None
            current_lines = [raw]
            continue
        if raw.startswith("+++ ") and current_rel is not None:
            plus_rel = _strip_ab_prefix(raw[4:].strip().split("\t", 1)[0])
            current_lines.append(raw)
            continue
        if current_rel is not None:
            current_lines.append(raw)
    if current_rel is not None and current_lines:
        blocks.append((plus_rel or current_rel, current_lines))
    return blocks


def _strip_ab_prefix(label: str) -> str:
    if label.startswith("a/") or label.startswith("b/"):
        return label[2:]
    return label


def _apply_hunks(original: str, diff_lines: list[str], rel: str) -> str:
    lines = original.splitlines()
    had_trailing_nl = original.endswith("\n") if original else True
    cursor = 0
    result: list[str] = []
    hunk_lines: list[str] = []
    old_start = 0

    def flush() -> None:
        nonlocal cursor, hunk_lines, old_start
        if not hunk_lines:
            return
        chunk, cursor = _apply_one_hunk(lines, cursor, old_start, hunk_lines, rel)
        result.extend(chunk)
        hunk_lines = []

    for raw in diff_lines:
        header = _HUNK_HEADER.match(raw)
        if header:
            flush()
            old_start = int(header.group(1))
            continue
        if raw.startswith("--- ") or raw.startswith("+++ "):
            continue
        if raw.startswith("\\"):
            continue
        if raw[:1] in {" ", "-", "+"}:
            hunk_lines.append(raw)

    flush()
    result.extend(lines[cursor:])
    text = "\n".join(result)
    if had_trailing_nl and (text or original):
        text += "\n"
    return text


def _apply_one_hunk(
    source: list[str],
    already_consumed: int,
    old_start: int,
    hunk: list[str],
    rel: str,
) -> tuple[list[str], int]:
    """Copy untouched prefix + hunk result. Returns (lines, new_source_index)."""
    expected_old = [line[1:] for line in hunk if line[:1] in {" ", "-"}]
    idx = _find_hunk(source, already_consumed, old_start, expected_old, rel)
    prefix = source[already_consumed:idx]
    rebuilt: list[str] = []
    src_i = idx
    for line in hunk:
        tag, body = line[:1], line[1:]
        if tag == " ":
            if src_i >= len(source) or source[src_i] != body:
                raise ValueError(f"{rel}: hunk context mismatch")
            rebuilt.append(body)
            src_i += 1
        elif tag == "-":
            if src_i >= len(source) or source[src_i] != body:
                raise ValueError(f"{rel}: hunk removal mismatch")
            src_i += 1
        elif tag == "+":
            rebuilt.append(body)
    return prefix + rebuilt, src_i


def _find_hunk(
    source: list[str],
    already_consumed: int,
    old_start: int,
    expected_old: list[str],
    rel: str,
) -> int:
    if not expected_old:
        return max(old_start - 1, already_consumed)
    stated = max(old_start - 1, 0)
    candidates = [stated]
    for fuzz in range(1, 4):
        candidates.extend((stated - fuzz, stated + fuzz))
    seen: set[int] = set()
    for idx in candidates:
        if idx in seen or idx < already_consumed:
            continue
        seen.add(idx)
        window = source[idx : idx + len(expected_old)]
        if window == expected_old:
            return idx
    for idx in range(already_consumed, len(source) - len(expected_old) + 1):
        if source[idx : idx + len(expected_old)] == expected_old:
            return idx
    raise ValueError(f"{rel}: could not match hunk starting at line {old_start}")
