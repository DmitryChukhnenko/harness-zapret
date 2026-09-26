import json
from subprocess import CompletedProcess

import pytest
from harness.probe import ProbeRequest, probe, remote_probe
from harness.strategy import corpus_dictionary, validate_expansion, validate_strategy


def test_forced_ip_preserves_name():
    def execute(args, **kwargs):
        assert "example.org:443:192.0.2.1" in args
        assert args[-1] == "https://example.org/"
        return CompletedProcess(args, 0, json.dumps({"http_code": 421, "remote_ip": "192.0.2.1"}))

    result = probe(ProbeRequest(domain="example.org", address="192.0.2.1"), execute)
    assert result["verdict"] == "ADDRESS_NOT_SERVING_HOST"


def test_client_unavailable():
    class Missing:
        def call(self, *args):
            raise OSError("offline")

    assert remote_probe(Missing(), ProbeRequest(domain="example.org"))["verdict"] == "UNMEASURED"


@pytest.mark.parametrize(
    "strategy", ["--x=$(id)", "--x=a;b", "--x='a>b'", "--lua-init=@code.lua", "--new", "--qnum=1"]
)
def test_deployment_strategy_rejected(strategy):
    with pytest.raises(ValueError):
        validate_strategy(strategy)


def test_corpus_bounds_grid(fact):
    dictionary = corpus_dictionary([fact(strategy="--lua-desync=multisplit:pos=1")])
    assert validate_expansion("--lua-desync=multisplit:pos=2", dictionary, [])
    with pytest.raises(ValueError):
        validate_expansion("--lua-desync=imaginary:pos=2", dictionary, [])
