import json
import uuid

import pytest
from harness.config import Config
from harness.pipeline import pipeline
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
