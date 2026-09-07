"""CLI: load a task fixture, call the stub planner, print a pending scorecard."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ops_agent import __version__
from ops_agent.agent import run as run_agent
from ops_agent.eval.fixtures import Fixture, load_fixture, load_fixtures
from ops_agent.eval.scorecard import build_scorecard, format_scorecard, score_result
from ops_agent.markers import YOU_IMPLEMENT_AGENT, YOU_IMPLEMENT_PLANNER
from ops_agent.models import AgentResult, Plan
from ops_agent.planner import plan as plan_task


def _call_planner(fixture: Fixture) -> Plan | None:
    try:
        return plan_task(fixture.task)
    except NotImplementedError as exc:
        print(f"planner: NotImplemented — {exc}")
        return None


def _call_agent(fixture: Fixture) -> AgentResult | None:
    try:
        return run_agent(fixture.task)
    except NotImplementedError as exc:
        print(f"agent: NotImplemented — {exc}")
        return None


def cmd_run(args: argparse.Namespace) -> int:
    fixture = load_fixture(args.fixture)
    task = fixture.task
    print(f"loaded fixture: {task.id}")
    print(f"workspace:      {task.workspace}")
    print(f"prompt:         {task.prompt}")
    if task.success_criteria:
        print("success criteria:")
        for item in task.success_criteria:
            print(f"  - {item}")
    print()

    plan = _call_planner(fixture)
    if plan is not None:
        print(f"plan steps ({len(plan.steps)}):")
        for step in plan.steps:
            print(f"  - {step}")

    result: AgentResult | None = None
    if args.agent:
        result = _call_agent(fixture)
    else:
        print(f"agent: skipped (pass --agent to invoke the stub). {YOU_IMPLEMENT_AGENT}")

    if args.strict and (plan is None or (args.agent and result is None)):
        print("strict: unimplemented planner/agent — exiting 2")
        return 2

    row = score_result(fixture, result)
    print()
    print(format_scorecard(build_scorecard((fixture,), {task.id: result} if result else None)))
    print(f"\nrow status: {row.status.value}  pass={row.pass_rate}  "
          f"cost={row.cost_usd}  latency={row.latency_ms}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    fixtures = load_fixtures()
    scorecard = build_scorecard(fixtures)
    if args.format == "json":
        payload = {
            "rows": [
                {
                    "task_id": row.task_id,
                    "status": row.status.value,
                    "pass_rate": row.pass_rate,
                    "cost_usd": row.cost_usd,
                    "latency_ms": row.latency_ms,
                    "notes": row.notes,
                }
                for row in scorecard.rows
            ],
            "disclaimer": scorecard.disclaimer,
        }
        print(json.dumps(payload, indent=2))
        return 0
    print(f"ops-agent eval: {len(fixtures)} labeled fixture(s)\n")
    for fix in fixtures:
        print(f"  {fix.task.id}: {fix.task.prompt}")
    print()
    print(format_scorecard(scorecard))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops-agent",
        description=(
            "Load a labeled coding/ops fixture and run the (stub) planner. "
            f"Core loop is not implemented yet: {YOU_IMPLEMENT_PLANNER}"
        ),
    )
    parser.add_argument("--version", action="version", version=f"ops-agent {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="load one fixture and call the stub planner")
    run_p.add_argument("fixture", help="fixture id (e.g. fix_off_by_one) or path")
    run_p.add_argument(
        "--agent",
        action="store_true",
        help="also invoke the stub agent loop (expected NotImplemented)",
    )
    run_p.add_argument(
        "--strict",
        action="store_true",
        help="exit 2 if planner/agent are still unimplemented (off for scaffold CI)",
    )
    run_p.set_defaults(func=cmd_run)

    eval_p = sub.add_parser("eval", help="print the local-fixture scorecard")
    eval_p.add_argument(
        "--format",
        choices=("terminal", "json"),
        default="terminal",
        help="scorecard output format",
    )
    eval_p.set_defaults(func=cmd_eval)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
