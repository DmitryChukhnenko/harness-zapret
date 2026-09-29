import json
import uuid

import pytest
from harness.config import Config
from harness.llm import MockProvider
from harness.pipeline import pipeline
from harness.runner import ingest
from harness.storage import Storage, write_json


def test_ingestion_failure_stops_llm(tmp_path, monkeypatch):
    config = Config(data_dir=str(tmp_path))
    store = Storage(tmp_path)
    run_id = str(uuid.uuid4())
    write_json(store.root / "raw" / f"{run_id}.json", {"status": "completed"})
    (store.root / "raw" / f"{run_id}.events.jsonl").write_text("corrupt record\n")
    monkeypatch.setattr(
        "harness.pipeline.llm", lambda *_: pytest.fail("LLM called after failed ingestion")
    )
    with pytest.raises(json.JSONDecodeError):
        pipeline(config, run_id)
    output = json.loads((store.root / "reports" / f"{run_id}.json").read_text())
    assert output["downstream"] == "STOPPED"


def test_archive_to_gates_to_llm_to_report(tmp_path, monkeypatch):
    config = Config(data_dir=str(tmp_path))
    store = Storage(tmp_path)
    runs = [str(uuid.uuid4()), str(uuid.uuid4())]
    strategies = ["--payload=http_req", "--payload=tls_client_hello"]
    for day, run_id in enumerate(runs, start=25):
        stamp = f"2026-09-{day}T01:00:00+00:00"
        items = []
        for strategy in strategies:
            for domain in ("example.org", "example.com"):
                items.extend(
                    [
                        ("begin", [domain, "curl_test_https_tls12", "4", strategy, "fixture"]),
                        ("address", ["192.0.2.1"]),
                        ("attempt", ["0"]),
                        ("address", ["192.0.2.2"]),
                        ("attempt", ["0"]),
                        ("end", ["0"]),
                    ]
                )
        events = "".join(
            json.dumps({"event": op, "args": args, "timestamp": stamp}) + "\n" for op, args in items
        )
        (store.root / "raw" / f"{run_id}.events.jsonl").write_text(events)
        (store.root / "raw" / f"{run_id}.log").write_text("RAW_SERVER_INSTRUCTION_SENTINEL")
        write_json(
            store.root / "raw" / f"{run_id}.json", {"status": "completed", "bypass_disabled": True}
        )
    ingest(tmp_path, runs[0])

    class API:
        def call(self, *_):
            return {"available": True, "route": [{"gateway": "172.31.0.2"}]}

    provider = MockProvider(
        ['{"abstain":false,"candidate_index":1,"reason":"fixture","risk":"low"}']
    )
    monkeypatch.setattr("harness.pipeline.control", lambda *_: API())
    monkeypatch.setattr("harness.pipeline.make_provider", lambda *_: provider)

    def recheck(*_):
        original = store.facts()[0]
        store.ingest(
            [original.model_copy(update={"run_id": str(uuid.uuid4()), "source": "recheck"})]
        )
        return {"missing": [], "fixture": True}

    monkeypatch.setattr("harness.pipeline.recheck", recheck)
    result = pipeline(config, runs[1])
    assert result["llm"]["response"]["candidate_index"] == 1
    assert result["llm"]["eligible_candidates"][1]["strategy"] == strategies[1]
    assert len(provider.requests) == 1
    assert (
        result["summary"]["gates"]
        == json.loads((store.root / "summaries" / f"{runs[1]}.json").read_text())["gates"]
    )
    assert max(g["runs"] for g in result["summary"]["gates"]) == 3
    sent = json.dumps(provider.requests)
    assert "RAW_SERVER_INSTRUCTION_SENTINEL" not in sent
    assert all(strategy not in sent for strategy in strategies)
    assert result["external_delivery"] == "NOT_CONFIGURED"
