import pytest
from harness.config import Config
from harness.deployment import Deployment
from harness.locking import BusyError, lock
from harness.recheck import missing_rechecks
from harness.reporting import report


def build(tmp_path, *, scheduled=True, fail=False):
    active = [True]

    def restart(strategy):
        active[0] = not (fail and strategy == "--payload=tls_client_hello")

    return Deployment(
        tmp_path,
        Config(),
        restart,
        lambda: active[0],
        lambda: {
            "gateway:example.org": {"verdict": "OPEN", "success_count": 2},
            "client:example.org": {"verdict": "OPEN", "success_count": 2},
        },
        lambda: scheduled,
    )


def test_deploy_backup_restore(tmp_path):
    engine = build(tmp_path)
    engine.write_strategy("--payload=http_req")
    state = engine.apply("--payload=tls_client_hello", eligible=True)
    assert state["status"] == "observing"
    assert (tmp_path / "backup.conf").read_text().strip() == "--payload=http_req"
    assert engine.rollback()["status"] == "rolled_back"
    assert engine.read() == "--payload=http_req"


def test_start_failure_immediate_rollback(tmp_path):
    engine = build(tmp_path, fail=True)
    engine.write_strategy("--payload=http_req")
    assert engine.apply("--payload=tls_client_hello", eligible=True)["status"] == "rolled_back"
    assert engine.read() == "--payload=http_req"


def test_each_deployment_refusal(tmp_path):
    engine = build(tmp_path)
    with lock(tmp_path / "operation.lock"), pytest.raises(BusyError):
        engine.apply("--payload=http_req", eligible=True)
    with pytest.raises(ValueError, match="watchdog"):
        build(tmp_path, scheduled=False).apply("--payload=http_req", eligible=True)
    engine.write_strategy("--payload=http_req")
    with pytest.raises(ValueError, match="already installed"):
        engine.apply("--payload=http_req", eligible=True)
    with pytest.raises(ValueError, match="interpreter"):
        engine.apply("--x=a;id", eligible=True)
    with pytest.raises(ValueError, match="gates"):
        engine.apply("--payload=tls_client_hello", eligible=False)


def test_missing_recheck_and_loud_delivery(tmp_path, caplog):
    assert missing_rechecks(["A", "B", "C"], ["A", "C"]) == ["B"]

    class BrokenSink:
        def deliver(self, payload):
            raise OSError("offline")

    result = report(tmp_path, "fixture", {}, BrokenSink())
    assert result["external_delivery"] == "FAILED"
    assert "REPORT_DELIVERY_FAILED" in caplog.text
