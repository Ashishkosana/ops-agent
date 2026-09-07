# Eval harness

Labeled **local** fixtures only. The scorecard prints `—` for pass rate, cost,
and latency until the agent loop is implemented. Do not paste production
numbers here.

Each fixture is a directory:

```
evals/fixtures/<id>/
  task.json       # id, prompt, success_criteria
  labels.json     # expected_files_changed, tests_should_pass, gold_hint
  workspace/      # tiny broken repo the agent is allowed to search/test/patch
```

`labels.json` is for the harness, not for the tools. The agent should not
need the gold hint to act — that hint exists so a future verifier policy
can be scored honestly.

| id | What is broken |
|---|---|
| `fix_off_by_one` | `inclusive_upto` drops the last integer |
| `failing_healthcheck` | probe hits `/status` but the service exposes `/health` |
| `broken_import` | `app.py` imports a name that does not exist |

Run:

```bash
ops-agent eval
ops-agent run fix_off_by_one
python -m ops_agent.eval
```
