import json
import os
import sqlite3
from pathlib import Path

from harness.models import Fact


def fact_json(fact: Fact) -> str:
    return fact.model_dump_json(exclude_computed_fields=True)


class Storage:
    def __init__(self, root):
        self.root = Path(root)
        for name in ("raw", "facts", "summaries", "reports", "state"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.path = self.root / "facts" / "facts.sqlite3"
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS facts (run_id TEXT, timestamp TEXT, "
                "sequence INTEGER, body TEXT NOT NULL, "
                "PRIMARY KEY (run_id, timestamp, sequence))"
            )

    def connect(self):
        return sqlite3.connect(self.path)

    def ingest(self, facts, rebuild=False):
        inserted = 0
        with self.connect() as db:
            if rebuild:
                db.execute("DELETE FROM facts")
            for fact in facts:
                key = (fact.run_id, fact.timestamp.isoformat(), fact.sequence)
                body = fact_json(fact)
                old = db.execute(
                    "SELECT body FROM facts WHERE run_id=? AND timestamp=? AND sequence=?", key
                ).fetchone()
                if old and old[0] != body:
                    raise ValueError("conflicting fact at an existing idempotency key")
                if not old:
                    db.execute("INSERT INTO facts VALUES (?, ?, ?, ?)", (*key, body))
                    inserted += 1
        self.export()
        return inserted

    def facts(self, since=None):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM facts ORDER BY timestamp, run_id, sequence")
            result = [Fact.model_validate_json(row[0]) for row in rows]
        return [f for f in result if since is None or f.timestamp > since]

    def export(self):
        path = self.root / "facts" / "facts.jsonl"
        path.write_text("".join(fact_json(f) + "\n" for f in self.facts()), encoding="utf-8")


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, default=str))


def write_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)
