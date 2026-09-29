"""Explicit isolated-lab diagnostic: real nfqws2, probes, faults and rollback.

Uses a separate deployment directory and shortened observation windows. The
admission precondition is a fixture; this is never two-date admission evidence.
Refuses a non-idle gateway and restores the empty live configuration on exit.
"""

import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from harness.config import Config, load_domains
from harness.control import Control
from harness.deployment import Deployment
from harness.locking import BusyError, lock
from harness.node_service import PROCESSES, live_strategy, nft, start, stop
from harness.probe import ProbeRequest, probe, remote_probe, resolve
from harness.storage import write_json

OLD = "--filter-tcp=443 --payload=tls_client_hello"
NEW = OLD + " --lua-desync=multisplit:pos=1"
FAULT_TABLE = "harness_live_fault"


def clear_fault():
    subprocess.run(
        ["nft", "delete", "table", "inet", FAULT_TABLE], capture_output=True, check=False
    )


def fault(address, port):
    clear_fault()
    nft(f"""table inet {FAULT_TABLE} {{
      chain output {{ type filter hook output priority -200; policy accept;
        ip daddr {address} tcp dport {port} reject with tcp reset
      }}
      chain forward {{ type filter hook forward priority -200; policy accept;
        ip daddr {address} tcp dport {port} reject with tcp reset
      }}
    }}""")


def running():
    process = PROCESSES.get("active")
    return process is not None and process.poll() is None


def main():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        raise RuntimeError("set HARNESS_LIVE_TESTS=1 in the isolated lab")
    root = Path("/state/live/lifecycle") / str(uuid.uuid4())
    root.mkdir(parents=True)
    evidence = {
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "FAIL",
        "scope": "real service/network; fixture admission, isolated state, shortened windows",
        "events": [],
        "path": str(root),
    }

    def record(name, value):
        evidence["events"].append({"at": time.time(), "name": name, "value": value})
        write_json(root / "result.json", evidence)

    domain = load_domains().all()[0]
    address = resolve(domain, 4)[0]
    request = ProbeRequest(domain=domain, address=address, timeout=3, attempts=2)
    client = Control("http://172.31.0.3:8080", timeout=10)

    def measure():
        results = {
            f"gateway:{domain}": probe(request),
            f"client:{domain}": remote_probe(client, request),
        }
        record("measurement", results)
        return results

    def make_engine(name, repair=5, observation=60, scheduled=True):
        config = Config()
        config.watchdog.repair_wait_seconds = repair
        config.watchdog.observation_seconds = observation
        engine = Deployment(root / name, config, start, running, measure, lambda: scheduled)
        engine.write_strategy(OLD)
        start(OLD)
        assert running()
        return engine

    with lock("/state/operation.lock"):
        existing = subprocess.run(["pgrep", "-x", "nfqws2"], capture_output=True)
        if live_strategy() or existing.returncode == 0:
            raise RuntimeError("lifecycle diagnostic requires an idle lab")
        try:
            assert all(x["verdict"] == "OPEN" for x in measure().values())
            engine = make_engine("guard")
            state = engine.apply(NEW, eligible=True)
            assert state["status"] == "observing" and len(state["guard"]) == 2
            record("apply", state)
            queues = Path("/proc/net/netfilter/nfnetlink_queue").read_text()
            assert any(row.split()[0] == "200" for row in queues.splitlines())
            record("nfqueue_registered", queues)
            assert engine.watchdog()["status"] == "observing"
            with lock(engine.root / "watchdog.lock"):
                try:
                    engine.watchdog()
                except BusyError:
                    record("overlap_rejected", True)
                else:
                    raise AssertionError("overlapping watchdog was allowed")
            assert engine.watchdog()["status"] == "observing"
            record("lock_released", True)

            fault("172.31.0.3", 8080)
            unavailable = engine.watchdog()
            assert unavailable["status"] == "observing"
            assert f"client:{domain}" in unavailable["unmeasured"]
            record("client_unavailable_no_rollback", unavailable)
            clear_fault()
            assert engine.watchdog()["status"] == "observing"

            fault(address, 443)
            first = engine.watchdog()
            assert first["status"] == "observing"
            record("single_failed_tick_no_rollback", first)
            second = engine.watchdog()
            assert second["status"] == "rolled_back" and engine.read() == OLD and running()
            record("guard_rollback_service_restored", second)
            clear_fault()
            assert all(x["verdict"] == "OPEN" for x in measure().values())

            engine = make_engine("repair", repair=5)
            fault(address, 443)
            state = engine.apply(NEW, eligible=True)
            assert len(state["repair"]) == 2
            waiting = engine.watchdog()
            assert waiting["status"] == "observing"
            record("repair_wait_not_expired", waiting)
            while time.time() < state["repair_deadline"]:
                time.sleep(0.2)
            rolled = engine.watchdog()
            assert rolled["status"] == "rolled_back" and running() and engine.read() == OLD
            record("repair_timeout_rollback", rolled)
            clear_fault()

            engine = make_engine("accepted", repair=1, observation=2)
            state = engine.apply(NEW, eligible=True)
            while time.time() < state["deadline"]:
                time.sleep(0.2)
            closed = engine.watchdog()
            assert closed["status"] == "accepted"
            record("observation_closed", closed)

            engine = make_engine("start_failure")
            failure = engine.apply("--invalid-diagnostic-option=1", eligible=True)
            assert failure["status"] == "rolled_back" and running() and engine.read() == OLD
            record("immediate_start_failure_rollback", failure)

            for name, strategy, scheduled in [
                ("already_installed", OLD, True),
                ("watchdog_not_scheduled", NEW, False),
                ("unsafe_strategy", "--payload=a;id", True),
            ]:
                engine = make_engine(name, scheduled=scheduled)
                try:
                    engine.apply(strategy, eligible=True)
                except ValueError:
                    assert engine.read() == OLD and running()
                    record(name + "_refused", True)
                else:
                    raise AssertionError(name + " accepted")
            with lock(engine.root / "operation.lock"):
                try:
                    engine.apply(NEW, eligible=True)
                except BusyError:
                    record("busy_operation_refused", True)
                else:
                    raise AssertionError("busy operation accepted")
            evidence["status"] = "PASS_LIVE"
        except Exception as exc:
            record("error", {"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            clear_fault()
            stop()
            evidence["restored_empty_live_strategy"] = live_strategy() == ""
            write_json(root / "result.json", evidence)
            print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
