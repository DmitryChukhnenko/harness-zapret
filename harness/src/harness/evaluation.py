"""Explicit, opt-in real-provider contract evaluation; never deploys anything."""

from datetime import UTC, datetime

from harness.llm import (
    Candidate,
    InvariantView,
    MistralProvider,
    SelectionSummary,
    select_candidate,
)
from harness.reporting import report
from harness.storage import Storage


def live_evaluation(config):
    summary = SelectionSummary(
        eligible_candidates=[
            Candidate(index=0, clean_wins=4, runs=2, dates=2, domain_count=2),
            Candidate(index=1, clean_wins=40, runs=10, dates=10, domain_count=2),
        ],
        invariants=[InvariantView(name="fixture_integrity", status="PASS")],
    )
    result = select_candidate(summary, MistralProvider(config.llm), config.llm)
    valid = result.status == "ok" and result.response is not None
    label = "llm-live-eval-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return report(
        Storage(config.data_dir).root,
        label,
        {
            "status": "PASS_LIVE" if valid else "FAIL",
            "model": config.llm.model,
            "scope": "structured selection API contract on a synthetic summary",
            "result": result.as_dict(),
        },
    )
