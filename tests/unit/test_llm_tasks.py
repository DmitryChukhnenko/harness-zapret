import json

import pytest
from harness.llm import MockProvider
from harness.llm_tasks import (
    AnnotationInput,
    GridInput,
    LossInput,
    PatchInput,
    annotate,
    draft_patch,
    expand_grid,
    loss_reason,
)


def test_annotation_and_abstention():
    data = AnnotationInput(probe_count=1, clean_wins=0, missing_rechecks=1, invariants=[])
    text = '{"abstain":false,"anomalies":["missing"],"budget_advice":[],"next_targets":[]}'
    assert annotate(data, MockProvider([text])).status == "ok"
    data.probe_count = 0
    assert annotate(data, MockProvider()).calls == 0


def test_patch_is_exact_draft_and_refuses_hallucination():
    data = PatchInput(symptom="incorrect constant", source="count = 1\n", check_results=["FAIL"])
    good = json.dumps(
        {
            "abstain": False,
            "replacements": [{"old": "count = 1", "new": "count = 2"}],
            "reason": "fix",
        }
    )
    assert draft_patch(data, MockProvider([good])).status == "ok"
    assert data.source == "count = 1\n"
    assert (
        draft_patch(data, MockProvider([good.replace("count = 1", "invented")])).status
        == "invalid_patch_target"
    )


def test_loss_priority_and_unknown_abstain():
    data = LossInput(
        measured=False, integrity_passed=False, baseline_changed=True, failures=10, thin_wins=2
    )
    assert loss_reason(data).response.reason == "UNMEASURED"
    data = LossInput(
        measured=True, integrity_passed=True, baseline_changed=False, failures=0, thin_wins=0
    )
    assert loss_reason(data).response.abstain


def test_grid_hallucinations_and_duplicates_rejected():
    data = GridInput(
        corpus_operations=["--lua-desync", "lua:multisplit", "lua:multisplit:pos"], measured_count=1
    )
    text = '{"abstain":false,"proposals":[[{"option":"--lua-desync","value":"multisplit:pos=2"}]]}'
    result, proposals = expand_grid(data, MockProvider([text]), [])
    assert result.status == "ok" and proposals == ["--lua-desync=multisplit:pos=2"]
    assert expand_grid(data, MockProvider([text]), proposals)[0].status == "invalid_grid_proposal"
    assert expand_grid(data, MockProvider([text.replace("multisplit", "invented")]), [])[1] == []


@pytest.mark.parametrize("lane", ["annotation", "patch", "grid"])
def test_other_lanes_malformed_then_abstain(lane):
    if lane == "annotation":
        data = AnnotationInput(probe_count=1, clean_wins=0, missing_rechecks=0, invariants=[])
        response = '{"abstain":true,"anomalies":[],"budget_advice":[],"next_targets":[]}'

        def call(provider):
            return annotate(data, provider)
    elif lane == "patch":
        data = PatchInput(symptom="unknown", source="x = 1", check_results=["UNKNOWN"])
        response = '{"abstain":true,"replacements":[],"reason":"insufficient evidence"}'

        def call(provider):
            return draft_patch(data, provider)
    else:
        data = GridInput(corpus_operations=["--payload"], measured_count=1)
        response = '{"abstain":true,"proposals":[]}'

        def call(provider):
            return expand_grid(data, provider, [])[0]

    assert call(MockProvider(["malformed", response])).response.abstain
    assert call(MockProvider(["malformed", "malformed"])).status == "invalid_response"
