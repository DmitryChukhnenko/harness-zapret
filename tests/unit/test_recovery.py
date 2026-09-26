import uuid
from datetime import UTC, datetime, timedelta

from harness.config import Config, Domains
from harness.gates import evaluate_gates
from harness.pipeline import remaining_window
from harness.runner import ingest
from harness.storage import Storage, fact_json


def test_midnight_does_not_create_another_run_date(fact):
    started = datetime(2026, 9, 25, 23, 59, tzinfo=UTC)
    facts = [
        fact(run_id="a", run_timestamp=started),
        fact(run_id="b", timestamp=started + timedelta(minutes=2), run_timestamp=started),
    ]
    gates = evaluate_gates(facts, Domains(classes={"x": ["example.org"]}), Config())
    assert "pending_more_dates" in gates[0].reasons


def test_rebuild_preserves_rechecks(fact, tmp_path):
    store = Storage(tmp_path)
    run_id = str(uuid.uuid4())
    path = tmp_path / "raw" / f"{run_id}.recheck.jsonl"
    path.write_text(fact_json(fact(run_id=run_id, source="recheck")) + "\n")
    assert ingest(tmp_path, run_id)["inserted"] == 1
    assert ingest(tmp_path, rebuild=True)["inserted"] == 1
    assert len(store.facts()) == 1


def test_sweep_window_crosses_midnight():
    config = Config()
    assert remaining_window(config, datetime(2026, 9, 26, 22, tzinfo=UTC)) == 5 * 3600
    assert remaining_window(config, datetime(2026, 9, 27, 2, tzinfo=UTC)) == 3600
    assert remaining_window(config, datetime(2026, 9, 27, 3, tzinfo=UTC)) == 0
