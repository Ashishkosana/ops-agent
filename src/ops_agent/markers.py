"""Shared ownership markers. Do not soften these — they are the contract."""

YOU_IMPLEMENT_PLANNER = (
    "YOU IMPLEMENT: core planner — Ashish owns and defends task decomposition."
)
YOU_IMPLEMENT_AGENT = (
    "YOU IMPLEMENT: agent loop — planner → tools → verifier. Ashish owns this."
)
YOU_IMPLEMENT_VERIFIER = (
    "YOU IMPLEMENT: verifier policy — accept/reject a run against labels and evidence."
)

LATER_STUB_PATCH = "LATER STUB: real patch application (write files inside the workspace)."
LATER_STUB_METERING = "LATER STUB: cost/latency metering from real tool/LLM usage."
LATER_STUB_MARKETPLACE = "LATER STUB: GitHub Action marketplace packaging."

PENDING = "—"
