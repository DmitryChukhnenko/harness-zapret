from datetime import timedelta

import pytest
from harness.clean_win import clean_win
from harness.config import Config, Domains
from harness.gates import evaluate_gates
from harness.storage import Storage


@pytest.mark.parametrize(
    "success,addresses,expected",
    [
        (2, ["192.0.2.1", "192.0.2.2"], True),
        (2, ["192.0.2.1"], False),
        (1, ["192.0.2.1", "192.0.2.2"], False),
        (2, [], False),
    ],
)
def test_clean_win(fact, success, addresses, expected):
    result = clean_win(fact(success_count=success, frontend_addresses=addresses))
    assert result[0] is expected
    if not addresses:
        assert result[1] == "no_recorded_addresses"


def test_dates_are_not_runs(fact):
    domains = Domains(classes={"sample": ["example.org"]})
    a, b = fact(), fact(run_id="run-2")
    assert "pending_more_dates" in evaluate_gates([a, b], domains, Config())[0].reasons
    b.timestamp += timedelta(days=1)
    assert evaluate_gates([a, b], domains, Config())[0].eligible
    assert not evaluate_gates([a, b, fact(verdict="BLOCKED_OR_FAILED")], domains, Config())[
        0
    ].eligible


def test_foreign_and_missing_coverage(fact):
    assert not clean_win(fact(record_type="foreign"))[0]
    domains = Domains(classes={"sample": ["example.org", "example.com"]})
    assert "missing_domain_coverage" in evaluate_gates([fact()], domains, Config())[0].reasons


def test_idempotency_and_conflict_transaction(fact, tmp_path):
    store = Storage(tmp_path)
    assert store.ingest([fact()]) == 1
    assert store.ingest([fact()]) == 0
    with pytest.raises(ValueError):
        store.ingest([fact(run_id="new"), fact(success_count=1)])
    assert len(store.facts()) == 1
