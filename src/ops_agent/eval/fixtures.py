"""Load labeled task fixtures from the repo-root `evals/fixtures/` tree."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ops_agent.models import Labels, Task


@dataclass(frozen=True)
class Fixture:
    task: Task
    labels: Labels
    root: Path


def repo_root() -> Path:
    """Walk up from this file (and cwd) until `evals/fixtures` + `pyproject.toml`."""
    candidates = [Path(__file__).resolve(), *Path(__file__).resolve().parents, Path.cwd()]
    seen: set[Path] = set()
    for start in candidates:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / "evals" / "fixtures").is_dir() and (parent / "pyproject.toml").is_file():
                return parent
    raise FileNotFoundError("could not find repo root (evals/fixtures + pyproject.toml)")


def fixtures_dir() -> Path:
    return repo_root() / "evals" / "fixtures"


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return {str(key): value for key, value in data.items()}


def load_fixture(name_or_path: str | Path) -> Fixture:
    """Load one fixture by id (`fix_off_by_one`) or by directory path."""
    raw = Path(name_or_path)
    root = raw if raw.is_dir() else fixtures_dir() / raw
    if not root.is_dir():
        raise FileNotFoundError(f"fixture not found: {name_or_path}")

    task_data = _load_json(root / "task.json")
    label_data = _load_json(root / "labels.json")
    workspace = (root / "workspace").resolve()
    if not workspace.is_dir():
        raise FileNotFoundError(f"fixture workspace missing: {workspace}")

    task_id = str(task_data["id"])
    criteria = task_data.get("success_criteria") or []
    if not isinstance(criteria, list):
        raise ValueError(f"{root}/task.json: success_criteria must be a list")

    expected = label_data.get("expected_files_changed") or []
    if not isinstance(expected, list):
        raise ValueError(f"{root}/labels.json: expected_files_changed must be a list")

    task = Task(
        id=task_id,
        prompt=str(task_data["prompt"]),
        workspace=workspace,
        success_criteria=tuple(str(item) for item in criteria),
        notes=str(task_data.get("notes") or ""),
    )
    labels = Labels(
        task_id=str(label_data.get("task_id") or task_id),
        expected_files_changed=tuple(str(item) for item in expected),
        tests_should_pass=bool(label_data.get("tests_should_pass", True)),
        gold_hint=str(label_data.get("gold_hint") or ""),
    )
    return Fixture(task=task, labels=labels, root=root.resolve())


def load_fixtures() -> tuple[Fixture, ...]:
    """Load every fixture directory under `evals/fixtures/`, sorted by id."""
    root = fixtures_dir()
    found: list[Fixture] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "task.json").is_file():
            found.append(load_fixture(child))
    if not found:
        raise FileNotFoundError(f"no fixtures in {root}")
    return tuple(found)
