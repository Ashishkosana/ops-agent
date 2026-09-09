from __future__ import annotations

import json

from ops_agent.cli import main


def test_run_loads_fixture_and_prints_plan(capsys) -> None:
    assert main(["run", "fix_off_by_one"]) == 0
    out = capsys.readouterr().out
    assert "loaded fixture: fix_off_by_one" in out
    assert "plan steps" in out
    assert "search_codebase" in out
    assert "run_tests" in out
    assert "apply_patch" in out
    assert "agent: skipped" in out
    assert "not_implemented" in out
    assert "—" in out


def test_run_agent_solves_off_by_one(capsys) -> None:
    assert main(["run", "fix_off_by_one", "--agent"]) == 0
    out = capsys.readouterr().out
    assert "loaded fixture: fix_off_by_one" in out
    assert "plan steps" in out
    assert "agent: implemented=True" in out
    assert "1/1" in out
    assert "pass" in out
    assert "not_implemented" not in out.split("row status:")[-1]


def test_run_strict_passes_on_repaired_fixture() -> None:
    assert main(["run", "broken_import", "--strict"]) == 0


def test_eval_terminal(capsys) -> None:
    assert main(["eval"]) == 0
    out = capsys.readouterr().out
    assert "fix_off_by_one" in out
    assert "failing_healthcheck" in out
    assert "broken_import" in out
    assert "1/1" in out
    assert "pass" in out


def test_eval_json_has_real_local_metrics(capsys) -> None:
    assert main(["eval", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["rows"]) == 3
    assert all(row["pass_rate"] == "1/1" for row in payload["rows"])
    assert all(row["status"] == "pass" for row in payload["rows"])
    assert all(row["cost_usd"] == "0.0000" for row in payload["rows"])
    assert all(row["latency_ms"].isdigit() for row in payload["rows"])
    assert "production" in payload["disclaimer"].lower()


def test_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --version should SystemExit")
    assert "0.1.0" in capsys.readouterr().out
