"""`python -m ops_agent.eval` — run every fixture and print the scorecard."""

from __future__ import annotations

from ops_agent.agent import run as run_agent
from ops_agent.eval.fixtures import load_fixtures
from ops_agent.eval.scorecard import build_scorecard, format_scorecard
from ops_agent.models import AgentResult


def main() -> int:
    fixtures = load_fixtures()
    print(f"ops-agent eval: {len(fixtures)} labeled fixture(s) (local only)\n")
    results: dict[str, AgentResult] = {}
    for fix in fixtures:
        print(f"  {fix.task.id}: {fix.task.prompt}")
        results[fix.task.id] = run_agent(fix.task)
    print()
    print(format_scorecard(build_scorecard(fixtures, results)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
