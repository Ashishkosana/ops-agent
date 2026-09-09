# Eval harness

Labeled **local** fixtures only. `ops-agent eval` runs the agent on each
workspace (temp copy) and prints pass / cost / latency from that run. Do
not paste production numbers here.

Each fixture is a directory:

```
evals/fixtures/<id>/
  task.json       # id, prompt, success_criteria
  labels.json     # expected_files_changed, tests_should_pass, gold_hint
  workspace/      # tiny broken repo the agent is allowed to search/test/patch
```

`labels.json` is for the harness, not for the tools. The agent does not
read `gold_hint`. The hint exists so a verifier policy can be scored
honestly in eval mode (expected files, tests should pass).

| id | What is broken |
|---|---|
| `fix_off_by_one` | `inclusive_upto` drops the last integer |
| `failing_healthcheck` | probe hits `/status` but the service exposes `/health` |
| `broken_import` | `app.py` imports a name that does not exist |

Run:

```bash
ops-agent eval
ops-agent run fix_off_by_one --agent
python -m ops_agent.eval
```
