"""Additional advisory lanes. Outputs are drafts and can never execute or deploy."""

import shlex
from typing import Literal

from pydantic import Field

from harness.config import StrictModel
from harness.llm import InvariantView, LLMResult, structured_call
from harness.strategy import validate_expansion


class AnnotationInput(StrictModel):
    probe_count: int = Field(ge=0)
    clean_wins: int = Field(ge=0)
    missing_rechecks: int = Field(ge=0)
    invariants: list[InvariantView]


class Annotation(StrictModel):
    abstain: bool
    anomalies: list[str] = Field(max_length=10)
    budget_advice: list[str] = Field(max_length=10)
    next_targets: list[str] = Field(max_length=10)


def annotate(data, provider, config=None):
    if not data.probe_count:
        return LLMResult(
            Annotation(abstain=True, anomalies=[], budget_advice=[], next_targets=[]),
            "deterministic_abstain",
        )
    return structured_call(
        provider,
        data,
        Annotation,
        "Annotate the supplied verdicts. Budget advice is advisory only.",
        config,
    )


class PatchInput(StrictModel):
    symptom: str = Field(max_length=1000)
    source: str = Field(max_length=10000)
    check_results: list[Literal["PASS", "FAIL", "UNKNOWN"]]


class Replacement(StrictModel):
    old: str = Field(min_length=1, max_length=10000)
    new: str = Field(max_length=10000)


class PatchDraft(StrictModel):
    abstain: bool
    replacements: list[Replacement] = Field(max_length=10)
    reason: str = Field(max_length=1000)


def draft_patch(data, provider, config=None):
    result = structured_call(
        provider,
        data,
        PatchDraft,
        "Return exact replacements for review, never a diff or command.",
        config,
    )
    if result.response:
        draft = data.source
        for replacement in result.response.replacements:
            if result.response.abstain or draft.count(replacement.old) != 1:
                result.response, result.status = None, "invalid_patch_target"
                return result
            draft = draft.replace(replacement.old, replacement.new, 1)
    return result  # Caller may save a candidate file; this lane never applies it.


class LossInput(StrictModel):
    measured: bool
    integrity_passed: bool
    baseline_changed: bool
    failures: int = Field(ge=0)
    thin_wins: int = Field(ge=0)


class LossReason(StrictModel):
    abstain: bool
    reason: Literal[
        "UNMEASURED",
        "MEASUREMENT_INTEGRITY",
        "BASELINE_CHANGED",
        "FAILURES",
        "THIN_WINS",
        "UNKNOWN",
    ]
    steps: list[str]


def loss_reason(data):
    priority = [
        (not data.measured, "UNMEASURED"),
        (not data.integrity_passed, "MEASUREMENT_INTEGRITY"),
        (data.baseline_changed, "BASELINE_CHANGED"),
        (data.failures > 0, "FAILURES"),
        (data.thin_wins > 0, "THIN_WINS"),
    ]
    reason = next((label for condition, label in priority if condition), "UNKNOWN")
    # The ordered arithmetic conditions already answer the question (T-12.5).
    return LLMResult(
        LossReason(
            abstain=reason == "UNKNOWN", reason=reason, steps=["collect fresh dual-point evidence"]
        ),
        "deterministic_reason",
    )


class GridInput(StrictModel):
    corpus_operations: list[str] = Field(max_length=1000)
    measured_count: int = Field(ge=0)


class Operation(StrictModel):
    option: str = Field(max_length=100)
    value: str = Field(max_length=1000)


class GridDraft(StrictModel):
    abstain: bool
    proposals: list[list[Operation]] = Field(max_length=10)


def expand_grid(data, provider, observed, config=None):
    if not data.corpus_operations:
        return LLMResult(GridDraft(abstain=True, proposals=[]), "deterministic_abstain"), []
    result = structured_call(
        provider,
        data,
        GridDraft,
        "Propose option/value combinations only within the corpus dictionary. "
        "No commands or executable strategy strings.",
        config,
    )
    strategies = []
    if result.response:
        try:
            if result.response.abstain and result.response.proposals:
                raise ValueError("abstention must not contain proposals")
            for proposal in result.response.proposals:
                strategy = shlex.join([f"{op.option}={op.value}" for op in proposal])
                strategies.append(
                    validate_expansion(
                        strategy, set(data.corpus_operations), set(observed) | set(strategies)
                    )
                )
        except ValueError:
            result.response, result.status = None, "invalid_grid_proposal"
            strategies = []
    return result, strategies
