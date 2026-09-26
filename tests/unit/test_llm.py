import json

import httpx
import pytest
from harness.llm import (
    MISTRAL_ENDPOINT,
    Candidate,
    Completion,
    InvariantView,
    MistralProvider,
    MockProvider,
    ProviderError,
    SelectionSummary,
    select_candidate,
)
from pydantic import ValidationError


def summary(n=2):
    return SelectionSummary(
        eligible_candidates=[
            Candidate(index=i, clean_wins=4, runs=2, dates=2, domain_count=2) for i in range(n)
        ],
        invariants=[InvariantView(name="measurement_integrity", status="PASS")],
    )


def answer(index=1, **changes):
    return json.dumps(
        dict(abstain=False, candidate_index=index, reason="Evidence", risk="low") | changes
    )


def test_official_mistral_request(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "unit-test-only")

    def handle(request):
        assert str(request.url) == MISTRAL_ENDPOINT
        assert request.method == "POST"
        assert request.headers["authorization"] == "Bearer unit-test-only"
        body = json.loads(request.content)
        assert body["model"] == "mistral-small-latest"
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
        assert "tools" not in body
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": answer()}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    result = select_candidate(summary(), MistralProvider(transport=httpx.MockTransport(handle)))
    assert result.response.candidate_index == 1
    assert result.usage["total_tokens"] == 15
    assert result.cost is None


def test_key_only_from_environment(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    with pytest.raises(ProviderError, match="MISTRAL_API_KEY"):
        MistralProvider().complete([], {})


@pytest.mark.parametrize("status", [301, 401, 429, 500])
def test_http_failures_do_not_leak_or_retry(monkeypatch, status):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, text="secret", headers={"Location": "https://evil.invalid"})

    result = select_candidate(summary(), MistralProvider(transport=httpx.MockTransport(handle)))
    assert result.status == "provider_error"
    assert len(calls) == 1
    assert "secret" not in json.dumps(result.as_dict())


def test_retry_exact_invalid_response_once():
    provider = MockProvider(
        [Completion("{broken", {"total_tokens": 5}), Completion(answer(), {"total_tokens": 6})]
    )
    result = select_candidate(summary(), provider)
    assert result.response.candidate_index == 1
    assert result.calls == 2
    assert result.usage["total_tokens"] == 11
    assert provider.requests[1]["messages"][-2]["content"] == "{broken"
    assert "json_invalid" in provider.requests[1]["messages"][-1]["content"]


def test_invalid_twice_stops():
    provider = MockProvider(["bad", "bad", answer()])
    assert select_candidate(summary(), provider).status == "invalid_response"
    assert len(provider.requests) == 2


@pytest.mark.parametrize("index", [-1, 2, 10000])
def test_invalid_index(index):
    provider = MockProvider([answer(index)])
    assert select_candidate(summary(), provider).status == "index_out_of_range"
    assert len(provider.requests) == 1


def test_abstain():
    result = select_candidate(summary(), MockProvider([answer(None, abstain=True, risk="unknown")]))
    assert result.response.abstain


@pytest.mark.parametrize(
    "bad",
    [
        answer(strategy="--invented"),
        answer(True),
        answer("1"),
        answer(None),
        answer(1, abstain=True),
    ],
)
def test_strict_schema(bad):
    assert select_candidate(summary(), MockProvider([bad, bad])).status == "invalid_response"


@pytest.mark.parametrize("n", [0, 1])
def test_no_question_no_call(n):
    provider = MockProvider()
    assert select_candidate(summary(n), provider).calls == 0
    assert not provider.requests


def test_raw_logs_cannot_cross_typed_boundary():
    with pytest.raises(ValidationError):
        SelectionSummary.model_validate(
            summary().model_dump() | {"raw_log": "malicious server text"}
        )
    data = summary()
    data.invariants[0].status = "UNKNOWN"
    assert select_candidate(data, MockProvider()).status == "deterministic_abstain"
