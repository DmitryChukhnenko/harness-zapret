import json
import shlex
import subprocess
import sys

from harness.reconcile import reconcile
from harness.reporting import report
from harness.storage import write_json


def test_argument_roundtrip():
    strategy = "--payload=tls_client_hello --out-range='s1<d1'"
    argv = shlex.split(strategy)
    process = subprocess.run(
        [sys.executable, "-c", "import sys,json; print(json.dumps(sys.argv[1:]))", *argv],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(process.stdout) == argv
    assert shlex.split(shlex.join(argv)) == argv


def test_successful_report_sink(tmp_path):
    class Sink:
        def __init__(self):
            self.received = []

        def deliver(self, payload):
            self.received.append(payload)

    sink = Sink()
    assert report(tmp_path, "fixture", {"clean_wins": 2}, sink)["external_delivery"] == "DELIVERED"
    assert sink.received[0]["clean_wins"] == 2


def test_reconcile_both_nodes(tmp_path):
    write_json(tmp_path / "state" / "expected.json", {"strategy": "expected"})

    class Node:
        strategy, route = "expected", "172.31.0.2"

        def call(self, verb):
            return (
                {"strategy": self.strategy}
                if verb == "get_config"
                else {"route": [{"gateway": self.route}], "available": True}
            )

    node = Node()
    assert reconcile(tmp_path, node)["status"] == "PASS"
    node.strategy = "manual_fix"
    assert reconcile(tmp_path, node)["status"] == "DRIFT"
    node.strategy, node.route = "expected", "172.31.0.1"
    assert reconcile(tmp_path, node)["status"] == "DRIFT"
