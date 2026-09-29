import json
import uuid

from harness import node_runtime


def test_expired_lease_never_records_a_candidate_win(tmp_path, monkeypatch):
    monkeypatch.setattr(node_runtime, "ROOT", tmp_path)
    monkeypatch.setattr(node_runtime, "start", lambda *args: True)
    monkeypatch.setattr(node_runtime, "set_exclusions", lambda *args: None)
    monkeypatch.setattr(node_runtime, "recover_expired", lambda **kwargs: None)
    monkeypatch.setattr(node_runtime, "candidate_status", lambda: True)

    def expire(*args):
        (tmp_path / "recheck-lease.json").unlink()
        return []

    monkeypatch.setattr(node_runtime, "measure_candidate", expire)
    request = node_runtime.RecheckRequest(
        run_id=str(uuid.uuid4()), class_name="example", strategies=["--payload=tls_client_hello"]
    )
    node_runtime.recheck_worker(request)
    status = json.loads((tmp_path / "runs" / request.run_id / "status.json").read_text())
    assert status["status"] == "failed"
    assert status["missing"] == request.strategies
