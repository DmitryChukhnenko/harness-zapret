"""Archive compact measured results and hashes; never infer absent live passes."""

import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    root = Path("data/reports")
    evidence = {
        "date": "2026-09-29",
        "environment": "Docker Desktop Linux engine 29.8.0; Windows host",
        "doctor": load(root / "doctor-20260929.json"),
        "control": load(root / "control-live.json"),
        "diagnostics": {},
        "scope": "Controlled lab diagnostics; no real two-date admission or paid Mistral call.",
    }
    for kind in ("blockcheck", "lifecycle", "recheck"):
        paths = list((root / "live" / kind).glob("*/result.json"))
        latest = max(paths, key=lambda path: load(path)["timestamp"])
        result = load(latest)
        evidence["diagnostics"][kind] = {
            "result": result,
            "archive": latest.parent.as_posix(),
            "sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in latest.parent.iterdir()
                if path.is_file() and path.suffix in {".json", ".jsonl", ".log"}
            },
            "previous_runs": [
                {"run": path.parent.name, "status": load(path)["status"]}
                for path in sorted(paths)
                if path != latest
            ],
        }
    target = Path("docs/evidence/live-20260929.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
