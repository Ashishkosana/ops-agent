# ops-agent

**A coding/ops agent you can score — planner → tools → verifier → scorecard.**

[![CI](https://github.com/Ashishkosana/ops-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashishkosana/ops-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

`ops-agent` is a **Milestone 1 scaffold**: a CLI and GitHub Action that load a
labeled task fixture, call a **stub planner**, and print a scorecard whose
pass rate / cost / latency stay `—` until the agent exists.

The hard parts are left for the owner on purpose:

| Module | Marker |
|---|---|
| `src/ops_agent/planner.py` | `YOU IMPLEMENT` — task decomposition |
| `src/ops_agent/agent.py` | `YOU IMPLEMENT` — planner → tools → verifier loop |
| `src/ops_agent/verifier.py` | `YOU IMPLEMENT` — accept/reject policy |

Do not generate those. Ashish has to own and defend them.

This repo **lifts the review-lens pattern** (multi-step agent + labeled eval
harness) without copying that project. [review-lens](https://github.com/Ashishkosana/review-lens)
reviews a diff. This one **acts** on a broken workspace.

There are **no production metrics** in this README. When numbers appear, they
will be computed live from `evals/fixtures/` — never hardcoded.

---

## Try it (no API key)

```bash
git clone https://github.com/Ashishkosana/ops-agent && cd ops-agent
pip install -e ".[dev]"
ops-agent run fix_off_by_one
ops-agent eval
```

Expected on the scaffold: the CLI loads the fixture, the planner raises
`NotImplementedError` (`YOU IMPLEMENT`), and the scorecard prints em-dashes.

```
loaded fixture: fix_off_by_one
planner: NotImplemented — YOU IMPLEMENT: core planner — ...
agent: skipped

ops-agent scorecard
fixture          pass  cost  latency  status
---------------  ----  ----  -------  ----------------
fix_off_by_one   —     —     —        not_implemented

Honest metrics only: local fixtures/evals. No production stats.
```

`python -m ops_agent.eval` prints the same pending table.

---

## Architecture

```
  labeled fixture (evals/fixtures/<id>)
           │
           ▼
        CLI / Action
           │
           ▼
     ┌─ planner ─┐          YOU IMPLEMENT
     │  Plan     │
     └────┬──────┘
          ▼
     tools (stubs that already run)
        search_codebase   read-only walk of the fixture workspace
        run_tests         mock by default; can pytest the workspace
        apply_patch       dry-run unified diff, path-escape rejected
          │
          ▼
     ┌─ verifier ─┐         YOU IMPLEMENT
     │  verdict   │
     └────┬──────┘
          ▼
     scorecard              pass rate · cost · latency
                            (— until implemented; then local fixtures only)
```

**Ports, not a monolith.** The agent loop will depend on a `Toolbelt`, not on
pytest or the filesystem directly. CI tests the wiring against safe mocks —
no network, no secrets, no writes outside a fixture workspace.

```
src/ops_agent/
  cli.py           # load fixture → stub planner → pending scorecard
  planner.py       # YOU IMPLEMENT
  agent.py         # YOU IMPLEMENT
  verifier.py      # YOU IMPLEMENT
  models.py        # Task, Plan, AgentResult, Scorecard (pure)
  tools/           # search / pytest / dry-run patch + later metering stub
  eval/            # fixture loader + scorecard printer
evals/fixtures/    # 3 labeled workspaces (see evals/README.md)
```

### Later stubs (not Milestone 1)

- Real patch application (`apply_patch(..., dry_run=False)`)
- Cost / latency metering (`tools/metering.py`)
- Action marketplace packaging (`action.yml` branding / release tags)

---

## How this differs from review-lens

Same *discipline*, different *job*.

| | [review-lens](https://github.com/Ashishkosana/review-lens) | ops-agent |
|---|---|---|
| Input | a git diff | a broken workspace + a prompt |
| Motion | read → comment | search → test → patch → re-test |
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

1. **I left the core blank on purpose.** A generated planner is not a take.
   The interesting design is: what is a step, when do you stop, what is
   enough evidence to pass.
2. **Same eval habit as review-lens.** Labeled fixtures, a printer that
   refuses to invent numbers, CI that stays green on the scaffold without
   lying that the agent works.
3. **Tools are a trust boundary.** Search is read-only. Tests default to a
   mock so CI does not shell out. Patches are dry-run and cannot `../`
   out of the workspace. Real writes are a later stub, not a silent default.
4. **Ops is in the fixtures, not just LeetCode.** `failing_healthcheck` is a
   wrong probe path. The loop should look the same for a bug-fix and a
   runbook-shaped repair.
5. **Scorecard is a product, not a screenshot.** Pass rate without cost and
   latency is how agents look cheap until the bill arrives. All three stay
   `—` until they are measured.

---

## CLI

```bash
ops-agent run fix_off_by_one           # load + stub planner (exit 0)
ops-agent run fix_off_by_one --agent   # also call the stub loop (exit 0)
ops-agent run fix_off_by_one --strict  # exit 2 while unimplemented
ops-agent eval                         # scorecard over all fixtures
ops-agent eval --format json
```

---

## GitHub Action

Composite Action in `action.yml`. Workflow CI (`.github/workflows/ci.yml`)
installs the package, runs ruff / mypy / pytest, then `ops-agent run` +
`ops-agent eval` on a fixture.

The Action **skips the unimplemented agent by default** (`skip-agent: true`)
so a green check means "scaffold works", not "the agent solved the task."
That distinction is the whole point.

```yaml
# after you implement the loop, pin a tag and drop skip-agent
- uses: Ashishkosana/ops-agent@main
  with:
    fixture: fix_off_by_one
    skip-agent: true
```

Marketplace packaging is a later stub.

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
