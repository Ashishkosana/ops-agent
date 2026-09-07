from __future__ import annotations

import json

from ops_agent.cli import main
from ops_agent.markers import YOU_IMPLEMENT_PLANNER


def test_run_loads_fixture_and_calls_stub_planner(capsys) -> None:
    assert main(["run", "fix_off_by_one"]) == 0
    out = capsys.readouterr().out
    assert "loaded fixture: fix_off_by_one" in out
    assert "planner: NotImplemented" in out
    assert "YOU IMPLEMENT" in out
    assert YOU_IMPLEMENT_PLANNER.split("—")[0].strip() in out or "YOU IMPLEMENT" in out
    assert "—" in out
    assert "not_implemented" in out
    assert "agent: skipped" in out


def test_run_agent_flag_invokes_stub_and_stays_green(capsys) -> None:
    assert main(["run", "failing_healthcheck", "--agent"]) == 0
    out = capsys.readouterr().out
    assert "planner: NotImplemented" in out
    assert "agent: NotImplemented" in out
    assert "—" in out


def test_run_strict_exits_2_while_unimplemented() -> None:
    assert main(["run", "broken_import", "--strict"]) == 2


def test_eval_terminal(capsys) -> None:
    assert main(["eval"]) == 0
    out = capsys.readouterr().out
    assert "fix_off_by_one" in out
    assert "failing_healthcheck" in out
    assert "broken_import" in out
    assert "—" in out


def test_eval_json_pending(capsys) -> None:
    assert main(["eval", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["rows"]) == 3
    assert all(row["pass_rate"] == "—" for row in payload["rows"])
    assert "production" in payload["disclaimer"].lower()


def test_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --version should SystemExit")
    assert "0.1.0" in capsys.readouterr().out
