"""CLI: load a task fixture, plan, optionally run the agent, print a scorecard."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ops_agent import __version__
from ops_agent.agent import run as run_agent
from ops_agent.eval.fixtures import Fixture, load_fixture, load_fixtures
from ops_agent.eval.scorecard import build_scorecard, format_scorecard, score_result
from ops_agent.models import AgentResult, Plan
from ops_agent.planner import plan as plan_task


def _call_planner(fixture: Fixture) -> Plan | None:
    try:
        return plan_task(fixture.task)
    except (NotImplementedError, RuntimeError) as exc:
        print(f"planner: error — {exc}")
        return None


def _call_agent(fixture: Fixture) -> AgentResult | None:
    try:
        return run_agent(fixture.task)
    except (NotImplementedError, RuntimeError) as exc:
        print(f"agent: error — {exc}")
        return None


def _print_agent_summary(result: AgentResult) -> None:
    verdict = result.verification
    verdict_txt = "n/a"
    if verdict is not None:
        verdict_txt = "accept" if verdict.passed else "reject"
    print(
        f"agent: implemented={result.implemented}  "
        f"tests={result.tests_passed}  "
        f"files={', '.join(result.files_changed) or '(none)'}  "
        f"latency_ms={result.latency_ms}  "
        f"cost_usd={result.cost_usd}  "
        f"verifier={verdict_txt}"
    )
    if result.notes:
        print(f"agent notes: {result.notes}")


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
        if plan.notes:
            print(f"plan notes: {plan.notes}")

    run_loop = bool(args.agent or args.strict)
    result: AgentResult | None = None
    if run_loop:
        result = _call_agent(fixture)
        if result is not None:
            print()
            _print_agent_summary(result)
    else:
        print("agent: skipped (pass --agent to run the loop, or --strict to require a pass)")

    if args.strict:
        failed = (
            plan is None
            or result is None
            or not result.implemented
            or result.verification is None
            or result.verification.passed is not True
        )
        if failed:
            print("strict: planner/agent/verifier did not accept this fixture — exiting 2")
            return 2

    row = score_result(fixture, result)
    results = {task.id: result} if result is not None else None
    print()
    print(format_scorecard(build_scorecard((fixture,), results)))
    print(
        f"\nrow status: {row.status.value}  pass={row.pass_rate}  "
        f"cost={row.cost_usd}  latency={row.latency_ms}"
    )
    return 0


def _run_all_fixtures() -> tuple[tuple[Fixture, ...], dict[str, AgentResult]]:
    fixtures = load_fixtures()
    results: dict[str, AgentResult] = {}
    for fix in fixtures:
        print(f"running {fix.task.id} ...", file=sys.stderr)
        outcome = run_agent(fix.task)
        results[fix.task.id] = outcome
        status = "pass" if outcome.verification and outcome.verification.passed else "fail"
        print(
            f"  -> {status}  tests={outcome.tests_passed}  "
            f"files={', '.join(outcome.files_changed) or '(none)'}  "
            f"latency_ms={outcome.latency_ms}  cost_usd={outcome.cost_usd}",
            file=sys.stderr,
        )
    print("", file=sys.stderr)
    return fixtures, results


def cmd_eval(args: argparse.Namespace) -> int:
    fixtures, results = _run_all_fixtures()
    scorecard = build_scorecard(fixtures, results)
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
            "Load a labeled coding/ops fixture, plan a repair, and optionally "
            "run the deterministic planner → tools → verifier loop."
        ),
    )
    parser.add_argument("--version", action="version", version=f"ops-agent {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="load one fixture and print a plan")
    run_p.add_argument("fixture", help="fixture id (e.g. fix_off_by_one) or path")
    run_p.add_argument(
        "--agent",
        action="store_true",
        help="run the planner → tools → verifier loop on a temp copy",
    )
    run_p.add_argument(
        "--strict",
        action="store_true",
        help="run the agent and exit 2 if the verifier rejects the run",
    )
    run_p.set_defaults(func=cmd_run)

    eval_p = sub.add_parser("eval", help="run every local fixture and print the scorecard")
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
