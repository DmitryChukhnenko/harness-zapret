import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from harness.parser import parse_events
from harness.storage import Storage, write_json


def sweep(control, domains, root, duration=3600):
    store = Storage(root)
    run_id = str(uuid.uuid4())
    started = datetime.now(UTC).isoformat()
    response = control.call(
        "run_blockcheck", {"run_id": run_id, "domains": domains, "duration": duration}
    )
    if response.get("run_id") != run_id:
        raise ValueError("measurement node returned a different run")
    deadline = time.monotonic() + duration + 60
    while time.monotonic() < deadline:
        status = control.call("run_status", {"run_id": run_id})
        if status["status"] in ("completed", "failed", "timed_out"):
            raw = control.call("run_result", {"run_id": run_id})
            (store.root / "raw" / f"{run_id}.log").write_text(raw["log"], encoding="utf-8")
            (store.root / "raw" / f"{run_id}.events.jsonl").write_text(
                raw["events"], encoding="utf-8"
            )
            write_json(
                store.root / "raw" / f"{run_id}.json",
                {"run_id": run_id, "timestamp": started, "domains": domains, **status},
            )
            return run_id
        time.sleep(1)
    raise TimeoutError("node did not finalize bounded sweep; analysis must not proceed")


def ingest(root, run_id=None, rebuild=False, since=None):
    store = Storage(root)
    paths = sorted((store.root / "raw").glob("*.events.jsonl"))
    if run_id is not None:
        paths = [store.root / "raw" / f"{uuid.UUID(run_id)}.events.jsonl"]
    facts, tail = [], 0
    for path in paths:
        label = path.name.removesuffix(".events.jsonl")
        parsed = parse_events(Path(path).read_text(encoding="utf-8"), label)
        facts.extend(f for f in parsed.facts if since is None or f.timestamp > since)
        tail += parsed.discarded_tail
    if rebuild and since is not None:
        raise ValueError("cannot combine full rebuild and incremental boundary")
    count = store.ingest(facts, rebuild=rebuild)
    result = {"inserted": count, "discarded_tail": tail, "run_id": run_id}
    write_json(store.root / "state" / "ingestion.json", result)
    return result
