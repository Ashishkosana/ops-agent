"""Hypothesize a minimal unified diff from test evidence + source.

The agent never sees fixture labels or gold hints. Strategies are general
(import error, string assert, exclusive range) and fail closed when the
evidence does not uniquely justify a rewrite.
"""

from __future__ import annotations

import ast
import difflib
import re
from pathlib import Path

from ops_agent.models import Task
from ops_agent.tools._paths import is_inside
from ops_agent.tools.search import _SKIP_DIRS

_IMPORT_ERR = re.compile(
    r"cannot import name ['\"]([^'\"]+)['\"] from ['\"]([^'\"]+)['\"]"
)
_ASSERT_EQ = re.compile(r"assert (.+) == (.+)")
_TEST_PREFIX = "test_"


def propose_diff(workspace: Path, task: Task, test_output: str) -> str | None:
    """Return a unified diff or None if no unique repair is justified."""
    _ = task  # prompt is reserved for future strategies; tests drive M2.
    for strategy in (
        _repair_import_error,
        _repair_string_assert,
        _repair_sequence_off_by_one,
    ):
        diff = strategy(workspace, test_output)
        if diff:
            return diff
    return None


def make_unified_diff(relative: str, old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    if old and not old.endswith("\n"):
        old_lines = [line if line.endswith("\n") else f"{line}\n" for line in old.splitlines()]
    if new and not new.endswith("\n"):
        new_lines = [line if line.endswith("\n") else f"{line}\n" for line in new.splitlines()]
    return "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        )
    )


def iter_source_files(workspace: Path) -> list[Path]:
    root = workspace.resolve()
    found: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not is_inside(root, path):
            continue
        if path.name.startswith(_TEST_PREFIX):
            continue
        found.append(path)
    return found


def _rel(workspace: Path, path: Path) -> str:
    return str(path.resolve().relative_to(workspace.resolve()))


def _parse_assert_eq(test_output: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw in test_output.splitlines():
        line = raw.strip().lstrip("E").strip()
        match = _ASSERT_EQ.search(line)
        if match:
            pairs.append((match.group(1).strip(), match.group(2).strip()))
    return pairs


def _literal(expr: str) -> object | None:
    try:
        value: object = ast.literal_eval(expr)
    except (SyntaxError, ValueError):
        return None
    return value


def _top_level_names(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return names


def _repair_import_error(workspace: Path, test_output: str) -> str | None:
    match = _IMPORT_ERR.search(test_output)
    if not match:
        return None
    bad_name, module = match.group(1), match.group(2)
    module_path = workspace.resolve() / f"{module}.py"
    if not module_path.is_file() or not is_inside(workspace, module_path):
        return None
    names = _top_level_names(module_path.read_text(encoding="utf-8"))
    defined = [name for name in names if name != bad_name]
    replacement = _pick_replacement_name(defined, test_output)
    if replacement is None:
        return None

    for path in iter_source_files(workspace):
        text = path.read_text(encoding="utf-8")
        imported = re.search(
            rf"\bfrom\s+{re.escape(module)}\s+import\s+{re.escape(bad_name)}\b",
            text,
        )
        if not imported and bad_name not in text:
            continue
        updated = _rename_identifier(text, bad_name, replacement)
        if updated != text:
            return make_unified_diff(_rel(workspace, path), text, updated)
    return None


def _pick_replacement_name(defined: list[str], test_output: str) -> str | None:
    if not defined:
        return None
    mentioned = [name for name in defined if name in test_output]
    if len(mentioned) == 1:
        return mentioned[0]
    if len(defined) == 1:
        return defined[0]
    return None


def _rename_identifier(source: str, old: str, new: str) -> str:
    return re.sub(rf"\b{re.escape(old)}\b", new, source)


def _repair_string_assert(workspace: Path, test_output: str) -> str | None:
    for left, right in _parse_assert_eq(test_output):
        actual = _literal(left)
        expected = _literal(right)
        if not isinstance(actual, str) or not isinstance(expected, str):
            continue
        old_tok, new_tok = _diff_tokens(actual, expected)
        diff = _replace_unique_token(workspace, old_tok, new_tok)
        if diff:
            return diff
        diff = _replace_unique_token(workspace, actual, expected)
        if diff:
            return diff
    return None


def _diff_tokens(actual: str, expected: str) -> tuple[str, str]:
    prefix = 0
    limit = min(len(actual), len(expected))
    while prefix < limit and actual[prefix] == expected[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < len(actual) - prefix
        and suffix < len(expected) - prefix
        and actual[len(actual) - 1 - suffix] == expected[len(expected) - 1 - suffix]
    ):
        suffix += 1
    old = actual[prefix : len(actual) - suffix if suffix else len(actual)]
    new = expected[prefix : len(expected) - suffix if suffix else len(expected)]
    if not old:
        return actual, expected
    return old, new


def _replace_unique_token(workspace: Path, old: str, new: str) -> str | None:
    if not old or old == new:
        return None
    hits: list[tuple[Path, str]] = []
    for path in iter_source_files(workspace):
        text = path.read_text(encoding="utf-8")
        if old in text:
            hits.append((path, text))
    if len(hits) != 1:
        return None
    path, text = hits[0]
    updated = text.replace(old, new)
    if updated == text:
        return None
    return make_unified_diff(_rel(workspace, path), text, updated)


def _repair_sequence_off_by_one(workspace: Path, test_output: str) -> str | None:
    for left, right in _parse_assert_eq(test_output):
        actual = _literal(left)
        expected = _literal(right)
        if not isinstance(actual, list) or not isinstance(expected, list):
            continue
        if actual == expected[:-1] and expected:
            return _inclusive_range_stop(workspace)
    return None


def _inclusive_range_stop(workspace: Path) -> str | None:
    """If a source file has range(x) (exclusive stop), bump to range(x + 1)."""
    for path in iter_source_files(workspace):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "range":
                continue
            if len(node.args) != 1:
                continue
            stop = node.args[0]
            if isinstance(stop, ast.BinOp) and isinstance(stop.op, ast.Add):
                continue
            old_seg = ast.get_source_segment(text, node)
            stop_seg = ast.get_source_segment(text, stop)
            if not old_seg or not stop_seg:
                continue
            new_seg = f"range({stop_seg} + 1)"
            updated = text.replace(old_seg, new_seg, 1)
            if updated != text:
                return make_unified_diff(_rel(workspace, path), text, updated)
    return None
