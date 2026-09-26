from datetime import UTC, datetime, timedelta

from harness.budget import allocate
from harness.config import Config


def test_budget_threshold_expiry_and_last_module(fact):
    config = Config()
    config.budget.zero_win_elimination_threshold = 2
    now = datetime(2026, 9, 26, tzinfo=UTC)
    facts = [
        fact(source="a", verdict="BLOCKED_OR_FAILED"),
        fact(source="a", sequence=1, verdict="BLOCKED_OR_FAILED"),
        fact(source="b"),
    ]
    output = allocate(facts, {}, now, config)
    assert ("https_tls12", "a") in output["disabled"]
    assert ("https_tls12", "b") in output["active"]
    output = allocate(facts, {"a": now - timedelta(days=15)}, now, config)
    assert ("https_tls12", "a") in output["active"]
    output = allocate(facts[:2], {}, now, config)
    assert output["active"] == [("https_tls12", "a")]
