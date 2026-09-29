"""Run on an idle zapret container: bounded upstream custom-grid diagnostic.

Archives are separate from admission history; this is not a full scheduled sweep.
"""

import json
import os
import shlex
import shutil
import signal
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from harness.config import load_config, load_domains
from harness.locking import lock
from harness.node_service import live_strategy
from harness.parser import parse_events
from harness.storage import fact_json, write_json


def main():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        raise RuntimeError("set HARNESS_LIVE_TESTS=1 in the isolated lab")
    config = load_config()
    run_id = str(uuid.uuid4())
    root = Path("/state/live/blockcheck") / run_id
    root.mkdir(parents=True)
    started = datetime.now(UTC).isoformat()
    strategies = [
        "--payload=tls_client_hello --lua-desync=multisplit:pos=1",
        "--out-range=s1<d1 --payload=tls_client_hello --lua-desync=multisplit:pos=1",
    ]
    modules = root / "modules" / "custom"
    modules.mkdir(parents=True)
    shutil.copyfile("/opt/zapret2/blockcheck2.d/custom/10-list.sh", modules / "10-list.sh")
    (modules / "list_https_tls12.txt").write_text("\n".join(strategies) + "\n")
    env = os.environ | {
        "BATCH": "1",
        "DOMAINS": load_domains().all()[0],
        "IPVS": "4",
        "TEST": "custom",
        "BLOCKCHECK2D": str(modules.parent),
        "REPEATS": str(config.measurement.attempts_per_domain),
        "PARALLEL": "0",
        "SCANLEVEL": "force",
        "SKIP_IPBLOCK": "1",
        "ENABLE_HTTP": "0",
        "ENABLE_HTTPS_TLS12": "1",
        "ENABLE_HTTPS_TLS13": "0",
        "ENABLE_HTTP3": "0",
        "HARNESS_EVENTS": str(root / "events.jsonl"),
        "HARNESS_RUN_TIMESTAMP": started,
        "CURL_MAX_TIME": str(config.timeouts.exit_probe_seconds),
    }
    with lock("/state/operation.lock"):
        existing = subprocess.run(["pgrep", "-x", "nfqws2"], capture_output=True)
        if live_strategy() or existing.returncode == 0:
            raise RuntimeError("smoke requires an idle lab without a deployed strategy")
        with (root / "raw.log").open("w") as output:
            process = subprocess.Popen(
                ["sh", "/opt/zapret2/blockcheck2.sh"],
                cwd="/opt/zapret2",
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                code = process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                code = 124
    events = root / "events.jsonl"
    parsed = parse_events(events.read_text() if events.exists() else "", run_id)
    (root / "facts.jsonl").write_text("".join(fact_json(f) + "\n" for f in parsed.facts))
    measured = [f for f in parsed.facts if f.record_type == "probe"]
    roundtrip = all(
        any(shlex.split(f.strategy) == shlex.split(sent) for f in measured) for sent in strategies
    )
    result = {
        "timestamp": started,
        "kind": "bounded_live_smoke_not_admission_evidence",
        "status": "PASS_LIVE" if code == 0 and roundtrip else "FAIL",
        "run_id": run_id,
        "exit_code": code,
        "facts": len(parsed.facts),
        "discarded_tail": parsed.discarded_tail,
        "argument_roundtrip": roundtrip,
        "sent": strategies,
        "observed": [f.strategy for f in measured],
        "path": str(root),
    }
    write_json(root / "result.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS_LIVE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
