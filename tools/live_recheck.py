"""Real dual-point candidate/active NFQUEUE and lease recovery on an idle lab."""

import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from harness.config import load_config, load_domains
from harness.locking import lock
from harness.node_runtime import client_control, recover_expired
from harness.node_service import (
    PROCESSES,
    candidate_status,
    live_strategy,
    set_exclusions,
    start,
    stop,
)
from harness.recheck import measure_candidate
from harness.storage import fact_json, write_json


def main():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        raise RuntimeError("set HARNESS_LIVE_TESTS=1 in the isolated lab")
    run_id = str(uuid.uuid4())
    root = Path("/state/live/recheck") / run_id
    root.mkdir(parents=True)
    lease = Path("/state/recheck-lease.json")
    domains = load_domains().all()
    strategy = "--payload=tls_client_hello --lua-desync=multisplit:pos=1"
    result = {
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "FAIL",
        "scope": "live candidate probes; separate diagnostic archive, no admission bypass",
        "path": str(root),
    }
    with lock("/state/operation.lock"):
        existing = subprocess.run(["pgrep", "-x", "nfqws2"], capture_output=True)
        if live_strategy() or existing.returncode == 0 or lease.exists():
            raise RuntimeError("requires idle lab")
        try:
            start("--payload=tls_client_hello")
            active_pid = PROCESSES["active"].pid
            write_json(lease, {"expires": time.time() + 120, "domains": domains})
            set_exclusions(domains)
            start(strategy, "candidate", domains)
            facts = measure_candidate(run_id, strategy, domains, client_control(), load_config())
            (root / "facts.jsonl").write_text("".join(fact_json(f) + "\n" for f in facts))
            assert candidate_status() and PROCESSES["active"].poll() is None
            assert len(facts) == len(domains) * 2
            assert all(f.verdict == "OPEN" and len(f.frontend_addresses) >= 2 for f in facts)
            result["facts"] = len(facts)
            result["points"] = sorted({f.measurement_point for f in facts})
            result["all_open_multiple_addresses"] = True
            write_json(lease, {"expires": time.time() - 1, "domains": domains})
            recover_expired()
            assert not candidate_status() and not lease.exists()
            assert PROCESSES["active"].pid == active_pid and PROCESSES["active"].poll() is None
            assert Path("/state/recheck-hosts.txt").read_text() == ""
            result["lease_restored_without_active_restart"] = True
            result["status"] = "PASS_LIVE"
        finally:
            recover_expired(force=True)
            stop("candidate")
            stop()
            write_json(root / "result.json", result)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
