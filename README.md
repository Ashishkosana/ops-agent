# ops-agent

**A coding/ops agent you can score — planner → tools → verifier → scorecard.**

[![CI](https://github.com/Ashishkosana/ops-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashishkosana/ops-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

`ops-agent` is a **Milestone 2** local repair loop: a CLI and GitHub Action
that load a labeled fixture, plan a finite search → test → patch → re-test
sequence, run it on a **temp copy** of the workspace, and print a scorecard
whose pass / cost / latency come from that run.

This is a scored toy on three labeled workspaces. It is **not** a production
ops platform and it does not have production traffic, user counts, or
Kafka-scale claims.

There are **no hardcoded production metrics** in this README. When the
scorecard prints numbers, they are computed live from `evals/fixtures/`.
Cost is `$0.0000` on the default planner because no model is called.
Latency is wall-clock milliseconds of that local run and will vary by machine.

---

## What works vs what is unfinished

| Piece | Status |
|---|---|
| Deterministic planner (`src/ops_agent/planner.py`) | Works offline. Finite plan from the task prompt. |
| Agent loop (`src/ops_agent/agent.py`) | Works. Temp workspace, tool budget, no infinite retry. |
| Verifier (`src/ops_agent/verifier.py`) | Works. Fail-closed: mock tests and missing evidence reject. |
| Tools: search / read / apply_patch / run_tests | Work. Path escape rejected. Safe mocks remain the Toolbelt default. |
| `ops-agent run` / `ops-agent eval` | Work. Eval runs every fixture and scores it. |
| Local scorecard | Works. Pass rate + measured cost/latency, or `—` if not measured. |
| LLM planner | Gated only. `OPS_AGENT_PLANNER=llm` requires a key and then **refuses** — this package ships no vendor client. CI stays offline. |
| Action marketplace packaging | Still a later stub (`action.yml` branding / release tags). |

The owner still has to defend the policy: what is a step, when to stop, and
what counts as evidence. The code is the take, not a hidden generator.

---

## Try it (no API key)

```bash
git clone https://github.com/Ashishkosana/ops-agent && cd ops-agent
pip install -e ".[dev]"
ops-agent run fix_off_by_one
ops-agent run fix_off_by_one --agent
ops-agent eval
```

`ops-agent run` prints the plan and a pending row (the loop is not invoked).
`--agent` runs the loop on a temp copy. `--strict` runs the loop and exits 2
if the verifier rejects.

`ops-agent eval` runs all three fixtures. Expect a scorecard shaped like:

```
ops-agent scorecard
fixture               pass  cost    latency  status
--------------------  ----  ------  -------  ------
broken_import         1/1   0.0000  <ms>     pass
failing_healthcheck   1/1   0.0000  <ms>     pass
fix_off_by_one        1/1   0.0000  <ms>     pass

Honest metrics only: local fixtures/evals. No production stats.
```

`<ms>` is whatever that process measured. Do not paste a latency from this
README into a resume as if it were a benchmark.

`python -m ops_agent.eval` prints the same scored table.

---

## Architecture

```
  labeled fixture (evals/fixtures/<id>)
           │
           ▼
        CLI / Action
           │
           ▼
     ┌─ planner ─┐          deterministic (LLM gated, offline CI)
     │  Plan     │
     └────┬──────┘
          ▼
     tools (temp copy of the workspace)
        search_codebase   read-only walk
        read_file         one file; path-escape rejected
        run_tests         mock by default; real pytest when safe_mocks=False
        apply_patch       dry-run by default; writes only on a validated diff
          │
          ▼
     ┌─ verifier ─┐         fail-closed (labels optional; gold hints unused)
     │  verdict   │
     └────┬──────┘
          ▼
     scorecard              pass rate · cost · latency
                            (local fixtures only)
```

**Ports, not a monolith.** The loop depends on a `Toolbelt`, not on pytest or
the filesystem directly. Unit tests can inject `safe_mocks=True`. Eval uses
real pytest + writes inside a temp directory — no network, no secrets, no
writes back into `evals/fixtures/`.

```
src/ops_agent/
  cli.py           # load fixture → plan → optional agent → scorecard
  planner.py       # deterministic decomposition (LLM path gated)
  agent.py         # planner → tools → verifier
  verifier.py      # accept / reject from evidence
  repair.py        # hypothesize a unified diff from test output
  models.py        # Task, Plan, AgentResult, Scorecard (pure)
  tools/           # search / read / pytest / patch + local metering
  eval/            # fixture loader + scorecard printer
evals/fixtures/    # 3 labeled workspaces (see evals/README.md)
```

---

## How this differs from review-lens

Same *discipline*, different *job*.

| | [review-lens](https://github.com/Ashishkosana/review-lens) | ops-agent |
|---|---|---|
| Input | a git diff | a broken workspace + a prompt |
| Motion | read → comment | search → read → test → patch → re-test |
| Verify | adversarially refute *findings* | policy over a *run* (tests, files, evidence) |
| Score | precision / recall / F1 on labeled diffs | pass rate, cost, latency on labeled tasks |
| Risk | noisy review comments | unbounded tool use, escaped patches, fake greens |
| Human | you decide what to merge | you decide the planner + verify policy |

review-lens taught: **precision beats recall**, and you *measure* the verify
pass on a labeled set instead of claiming it. ops-agent keeps that honesty
and adds a write-path: the agent can change code, so the verifier has to
be fail-closed about evidence, not vibes.

---

## Interview talking points

1. **Finite plan, not an open loop.** Search what the prompt names, run tests
   for evidence, apply one hypothesized patch, re-test. If it is still red,
   we stop. A tool-call budget is the backstop.
2. **Same eval habit as review-lens.** Labeled fixtures. The printer refuses
   to invent production numbers. Cost is $0.0000 here because no model ran;
   latency is measured wall-clock.
3. **Tools are a trust boundary.** Search and read are contained. Tests
   default to a mock so unit tests do not shell out. Patches cannot `../`
   out of the workspace. Real writes happen on a temp copy.
4. **Gold hints are not a cheat code.** `labels.json` is for the harness.
   The planner, repairer, and agent do not read `gold_hint`. The verifier
   may use expected files in eval mode; it never treats a hint as evidence.
5. **Ops is in the fixtures, not just LeetCode.** `failing_healthcheck` is a
   wrong probe path. The loop is the same for a bug-fix and a runbook-shaped
   repair. That is still three tiny repos — not a production ops story.

---

## CLI

```bash
ops-agent run fix_off_by_one           # load + plan (exit 0)
ops-agent run fix_off_by_one --agent   # run the loop on a temp copy
ops-agent run fix_off_by_one --strict  # run the loop; exit 2 if rejected
ops-agent eval                         # scorecard over all fixtures
ops-agent eval --format json
```

---

## GitHub Action

Composite Action in `action.yml`. Workflow CI (`.github/workflows/ci.yml`)
installs the package, runs ruff / mypy / pytest, then `ops-agent run --agent`
and `ops-agent eval` on the labeled fixtures.

`skip-agent` defaults to `false` now that the loop exists. Set it `true` if
you only want the planner + pending row.

```yaml
- uses: Ashishkosana/ops-agent@main
  with:
    fixture: fix_off_by_one
    skip-agent: false
```

Marketplace packaging is still a later stub.

---

## Dev

```bash
pip install -e ".[dev]"
ruff check src tests
mypy
pytest -q
```

Python 3.12+. Optional Docker:

```bash
docker build -t ops-agent .
docker run --rm ops-agent eval
```

---

## License

MIT © Ashish Kosana
