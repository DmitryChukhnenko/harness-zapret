import json
import threading
import time
from pathlib import Path

from harness.config import load_config, load_domains
from harness.control import Control
from harness.deployment import Deployment
from harness.gates import evaluate_gates
from harness.locking import BusyError, lock
from harness.models import Fact
from harness.node_runs import RunRef
from harness.node_service import live_strategy, service_status, set_exclusions, start, stop
from harness.parser import parse_events
from harness.probe import ProbeRequest, probe, remote_probe
from harness.recheck import measure_candidate, missing_rechecks
from harness.storage import fact_json, write_json
from harness.strategy import validate_strategy

ROOT = Path("/state")
HEARTBEAT = 0.0


def client_control():
    cfg = load_config()
    return Control(
        "http://172.31.0.3:8080",
        timeout=(cfg.timeouts.exit_probe_seconds + 1) * cfg.measurement.attempts_per_domain + 2,
    )


def measure_all():
    config, observations = load_config(), {}
    for domain in load_domains().all():
        request = ProbeRequest(
            domain=domain,
            attempts=config.measurement.attempts_per_domain,
            timeout=config.timeouts.exit_probe_seconds,
        )
        observations[f"gateway:{domain}"] = probe(request)
        observations[f"client:{domain}"] = remote_probe(client_control(), request)
    return observations


def engine():
    config = load_config()
    return Deployment(
        ROOT,
        config,
        start,
        service_status,
        measure_all,
        lambda: time.monotonic() - HEARTBEAT < config.watchdog.tick_seconds * 2,
    )


def archive_facts():
    facts = []
    for path in (ROOT / "runs").glob("*/events.jsonl"):
        facts.extend(parse_events(path.read_text(), path.parent.name).facts)
    for path in (ROOT / "runs").glob("*/recheck.jsonl"):
        facts.extend(Fact.model_validate_json(line) for line in path.read_text().splitlines())
    return facts


class ApplyRequest(RunRef):
    strategy: str
    class_name: str


def apply(payload):
    request = ApplyRequest.model_validate(payload)
    validate_strategy(request.strategy)
    facts = archive_facts()
    gates = evaluate_gates(facts, load_domains(), load_config())
    eligible = any(
        g.eligible and g.strategy == request.strategy and g.class_name == request.class_name
        for g in gates
    )
    # Require a completed dual-point recheck, not an LLM assertion of eligibility.
    members = load_domains().classes.get(request.class_name, [])
    for domain in members:
        for point in ("gateway", "client"):
            matching = [
                f
                for f in facts
                if f.run_id == request.run_id
                and f.source == "recheck"
                and f.strategy == request.strategy
                and f.domain == domain
                and f.measurement_point == point
            ]
            eligible = eligible and bool(matching) and all(f.verdict == "OPEN" for f in matching)
    return engine().apply(request.strategy, eligible=eligible)


def recover_expired(force=False):
    path = ROOT / "recheck-lease.json"
    if path.exists():
        lease = json.loads(path.read_text())
        if force or lease["expires"] <= time.time():
            stop("candidate")
            set_exclusions([])
            path.unlink()


def background():
    global HEARTBEAT
    config = load_config()
    while True:
        HEARTBEAT = time.monotonic()
        try:
            recover_expired()
            result = engine().watchdog()
            print(
                json.dumps(
                    {
                        "timestamp": time.time(),
                        "component": "watchdog",
                        "event": "tick",
                        "result": result["status"],
                    }
                ),
                flush=True,
            )
        except BusyError:
            pass
        except Exception:
            print(
                json.dumps(
                    {
                        "timestamp": time.time(),
                        "component": "watchdog",
                        "event": "tick",
                        "result": "ERROR",
                    }
                ),
                flush=True,
            )
        time.sleep(config.watchdog.tick_seconds)


def startup():
    recover_expired(force=True)
    deploy = engine()
    if deploy.state()["status"] in {"prepared", "observing", "rollback_required"}:
        deploy.rollback("node_restarted_during_observation")
    else:
        start(live_strategy())
    threading.Thread(target=background, daemon=True).start()


class RecheckRequest(RunRef):
    strategies: list[str]
    class_name: str


def recheck_worker(request):
    directory = ROOT / "runs" / request.run_id
    directory.mkdir(parents=True, exist_ok=False)
    facts, returned = [], []
    try:
        with lock(ROOT / "operation.lock"):
            config = load_config()
            domains = load_domains().classes[request.class_name]
            write_json(directory / "status.json", {"status": "running"})
            for strategy in request.strategies:
                duration = (
                    len(domains)
                    * config.measurement.min_distinct_addresses
                    * 2
                    * (config.timeouts.exit_probe_seconds + 2)
                    * config.measurement.attempts_per_domain
                    + 60
                )
                write_json(
                    ROOT / "recheck-lease.json",
                    {"expires": time.time() + duration, "domains": domains},
                )
                try:
                    set_exclusions(domains)
                    start(strategy, "candidate", domains)
                    measured = measure_candidate(
                        request.run_id, strategy, domains, client_control(), config, len(facts)
                    )
                    facts.extend(measured)
                    returned.append(strategy)
                finally:
                    recover_expired(force=True)
            (directory / "recheck.jsonl").write_text("".join(fact_json(f) + "\n" for f in facts))
            write_json(
                directory / "status.json",
                {"status": "completed", "missing": missing_rechecks(request.strategies, returned)},
            )
    except Exception:
        write_json(
            directory / "status.json",
            {"status": "failed", "missing": missing_rechecks(request.strategies, returned)},
        )


def recheck(payload):
    request = RecheckRequest.model_validate(payload)
    if request.class_name not in load_domains().classes or not 1 <= len(request.strategies) <= 10:
        raise ValueError("invalid recheck class or candidate count")
    observed = {f.strategy for f in archive_facts() if f.record_type == "probe"}
    for strategy in request.strategies:
        validate_strategy(strategy)
        if strategy not in observed:
            raise ValueError("recheck strategy is not in the measured corpus")
    if (ROOT / "runs" / request.run_id).exists():
        raise ValueError("run already exists")
    threading.Thread(target=recheck_worker, args=(request,), daemon=True).start()
    return {"run_id": request.run_id}
