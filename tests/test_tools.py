from __future__ import annotations

from pathlib import Path

from ops_agent.eval.fixtures import load_fixture
from ops_agent.markers import LATER_STUB_PATCH
from ops_agent.models import ToolName
from ops_agent.tools import Toolbelt, apply_patch, run_tests, search_codebase
from ops_agent.tools._paths import resolve_inside
from ops_agent.tools.patch import apply_patch_for_real


def test_search_finds_symbol_in_fixture() -> None:
    fixture = load_fixture("fix_off_by_one")
    result = search_codebase(fixture.task.workspace, "inclusive_upto")
    assert result.ok
    assert result.name is ToolName.SEARCH_CODEBASE
    assert "ranges.py" in result.metadata["files"]
    assert "inclusive_upto" in result.output


def test_search_empty_query() -> None:
    fixture = load_fixture("broken_import")
    result = search_codebase(fixture.task.workspace, "   ")
    assert result.ok is False


def test_search_miss() -> None:
    fixture = load_fixture("failing_healthcheck")
    result = search_codebase(fixture.task.workspace, "definitely-not-a-symbol")
    assert result.ok
    assert "no matches" in result.output


def test_run_tests_mock_does_not_execute() -> None:
    fixture = load_fixture("fix_off_by_one")
    result = run_tests(fixture.task.workspace, mock=True)
    assert result.ok
    assert result.metadata["mock"] is True
    assert "not executed" in result.output


def test_apply_patch_dry_run_records_files(tmp_path: Path) -> None:
    (tmp_path / "ranges.py").write_text("x = 1\n", encoding="utf-8")
    diff = """\
--- a/ranges.py
+++ b/ranges.py
@@ -1 +1 @@
-x = 1
+x = 2
"""
    result = apply_patch(tmp_path, diff, dry_run=True)
    assert result.ok
    assert result.metadata["wrote"] is False
    assert result.metadata["files"] == ["ranges.py"]
    assert (tmp_path / "ranges.py").read_text(encoding="utf-8") == "x = 1\n"


def test_apply_patch_rejects_path_escape(tmp_path: Path) -> None:
    diff = """\
--- a/../../etc/passwd
+++ b/../../etc/passwd
@@ -1 +1 @@
-root
+rooted
"""
    result = apply_patch(tmp_path, diff, dry_run=True)
    assert result.ok is False
    assert "escapes workspace" in result.output


def test_apply_patch_rejects_non_diff(tmp_path: Path) -> None:
    result = apply_patch(tmp_path, "just delete everything", dry_run=True)
    assert result.ok is False
    assert "unified diff" in result.output


def test_apply_patch_for_real_is_later_stub(tmp_path: Path) -> None:
    result = apply_patch_for_real(tmp_path, "--- a/x\n+++ b/x\n")
    assert result.ok is False
    assert LATER_STUB_PATCH in result.output


def test_resolve_inside_blocks_escape(tmp_path: Path) -> None:
    try:
        resolve_inside(tmp_path, "../secret")
    except ValueError as exc:
        assert "escapes workspace" in str(exc)
    else:
        raise AssertionError("expected path escape to fail")


def test_toolbelt_safe_defaults() -> None:
    fixture = load_fixture("failing_healthcheck")
    belt = Toolbelt(workspace=fixture.task.workspace)
    assert belt.safe_mocks is True
    search = belt.search_codebase("/status")
    assert search.ok
    tests = belt.run_tests()
    assert tests.metadata["mock"] is True
    patch = belt.apply_patch("--- a/healthcheck.py\n+++ b/healthcheck.py\n")
    assert patch.ok
    assert patch.metadata["wrote"] is False
