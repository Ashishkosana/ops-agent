"""`python -m ops_agent.eval` — print the fixture list and pending scorecard."""

from __future__ import annotations

from ops_agent.eval.fixtures import load_fixtures
from ops_agent.eval.scorecard import build_scorecard, format_scorecard


def main() -> int:
    fixtures = load_fixtures()
    print(f"ops-agent eval: {len(fixtures)} labeled fixture(s) (local only)\n")
    for fix in fixtures:
        print(f"  {fix.task.id}: {fix.task.prompt}")
    print()
    print(format_scorecard(build_scorecard(fixtures)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
