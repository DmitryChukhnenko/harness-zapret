import json

import pytest
from harness.parser import parse_events


def events(items):
    return "".join(
        json.dumps({"event": op, "args": args, "timestamp": "2026-09-26T00:00:00+00:00"}) + "\n"
        for op, args in items
    )


def test_completed_probe_and_tail():
    begin = ("begin", ["example.org", "curl_test_https_tls12", "4", "--x='a>b'", "module"])
    raw = events(
        [
            begin,
            ("address", ["192.0.2.1"]),
            ("attempt", ["0"]),
            ("address", ["192.0.2.2"]),
            ("attempt", ["0"]),
            ("end", ["0"]),
            begin,
        ]
    )
    parsed = parse_events(raw, "run")
    assert parsed.discarded_tail == 1
    assert parsed.facts[0].strategy == "--x='a>b'"
    assert parsed.facts[0].frontend_address_count == 2
    assert parsed.facts[0].success_count == 2


def test_corruption_is_not_a_success():
    with pytest.raises(json.JSONDecodeError):
        parse_events("not JSON\n", "run")
