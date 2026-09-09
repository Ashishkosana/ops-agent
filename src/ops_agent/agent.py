"""Agent loop: planner → tools → verifier.

Stop conditions (defend these):

- The plan is finite. We execute its steps once; we do not retry until green.
- A hard tool-call budget (`MAX_TOOL_CALLS`) stops runaway search/read.
- Patches and reads go through the Toolbelt, which refuses `../` escapes.
- The workspace the tools see is a temp copy of the fixture, so eval never
  mutates `evals/fixtures/`.
- Verifier is fail-closed: mock tests and missing evidence are rejects.

Default tools are real (`safe_mocks=False`) so a fixture can actually be
repaired. Callers that pass a Toolbelt keep that belt (unit tests stay mocked).
"""

from __future__ import annotations

import shutil
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from ops_agent.models import AgentResult, Task, ToolName, ToolResult
from ops_agent.planner import extract_search_queries
from ops_agent.planner import plan as plan_task
from ops_agent.repair import propose_diff
from ops_agent.tools.base import Toolbelt
from ops_agent.tools.metering import record_usage
from ops_agent.tools.metering import reset as reset_meter
from ops_agent.verifier import verify

MAX_TOOL_CALLS = 16
_TEST_PREFIX = "test_"


def run(task: Task, tools: Toolbelt | None = None) -> AgentResult:
    """Execute one task end-to-end."""
    reset_meter()
    started = time.perf_counter()
    if tools is None:
        with tempfile.TemporaryDirectory(prefix="ops-agent-") as tmp:
            dest = Path(tmp) / "workspace"
            shutil.copytree(task.workspace, dest)
            bound = Toolbelt(workspace=dest, safe_mocks=False)
            result = _run_loop(replace(task, workspace=dest), bound)
    else:
        result = _run_loop(task, tools)

    latency_ms = max(0, int((time.perf_counter() - started) * 1000))
    record_usage(tokens_in=0, tokens_out=0, latency_ms=latency_ms)
    # Deterministic path: no tokens, so cost is measured $0.0000 — not a guess.
    priced = replace(result, latency_ms=latency_ms, cost_usd=0.0)
    verdict = verify(task, priced, labels=None)
    return replace(priced, verification=verdict, notes="; ".join(verdict.reasons))


def _run_loop(task: Task, tools: Toolbelt) -> AgentResult:
    planned = plan_task(task)
    calls: list[ToolResult] = []
    files_changed: list[str] = []
    tests_passed: bool | None = None
    last_test_output = ""

    for step in planned.steps:
        if len(calls) >= MAX_TOOL_CALLS:
            break
        produced, last_test_output, tests_passed = _dispatch_step(
            task,
            tools,
            step,
            last_test_output,
            tests_passed,
            remaining=MAX_TOOL_CALLS - len(calls),
        )
        calls.extend(produced)
        for result in produced:
            if result.name is ToolName.APPLY_PATCH and result.ok:
                for rel in result.metadata.get("files", []):
                    if isinstance(rel, str) and rel not in files_changed:
                        files_changed.append(rel)

    return AgentResult(
        task_id=task.id,
        implemented=True,
        plan=planned,
        tool_calls=tuple(calls),
        files_changed=tuple(files_changed),
        tests_passed=tests_passed,
    )


def _dispatch_step(
    task: Task,
    tools: Toolbelt,
    step: str,
    last_test_output: str,
    tests_passed: bool | None,
    *,
    remaining: int,
) -> tuple[list[ToolResult], str, bool | None]:
    name, arg = _parse_step(step)
    if name == ToolName.SEARCH_CODEBASE.value:
        result = tools.search_codebase(arg or _fallback_query(task))
        extra = _read_search_hits(tools, result, remaining=remaining - 1)
        return [result, *extra], last_test_output, tests_passed
    if name == ToolName.READ_FILE.value and arg:
        return [tools.read_file(arg)], last_test_output, tests_passed
    if name == ToolName.RUN_TESTS.value:
        result = tools.run_tests()
        passed = None if result.metadata.get("mock") is True else result.ok
        return [result], result.output, passed
    if name == ToolName.APPLY_PATCH.value:
        patched = _apply_hypothesized_patch(task, tools, last_test_output)
        return [patched], last_test_output, tests_passed
    unknown = ToolResult(
        name=ToolName.SEARCH_CODEBASE,
        ok=False,
        output=f"unknown plan step: {step}",
    )
    return [unknown], last_test_output, tests_passed


def _parse_step(step: str) -> tuple[str, str]:
    name, sep, arg = step.partition(":")
    if sep:
        return name.strip(), arg.strip()
    return step.strip(), ""


def _fallback_query(task: Task) -> str:
    queries = extract_search_queries(task.prompt)
    return queries[0] if queries else "def"


def _read_search_hits(
    tools: Toolbelt,
    search: ToolResult,
    *,
    remaining: int,
) -> list[ToolResult]:
    """Read non-test files the search hit. Bounded by the leftover budget."""
    extra: list[ToolResult] = []
    files = search.metadata.get("files")
    if not isinstance(files, list) or remaining <= 0:
        return extra
    for item in files:
        if len(extra) >= remaining:
            break
        if not isinstance(item, str) or Path(item).name.startswith(_TEST_PREFIX):
            continue
        extra.append(tools.read_file(item))
    return extra


def _apply_hypothesized_patch(task: Task, tools: Toolbelt, test_output: str) -> ToolResult:
    diff = propose_diff(tools.workspace, task, test_output)
    if not diff:
        return ToolResult(
            name=ToolName.APPLY_PATCH,
            ok=False,
            output="no unique repair justified by test evidence",
            metadata={"files": [], "wrote": False},
        )
    return tools.apply_patch(diff)
