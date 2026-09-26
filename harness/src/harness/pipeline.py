import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from harness.config import load_domains
from harness.control import Control
from harness.gates import evaluate_gates
from harness.invariants import evaluate_invariants
from harness.llm import SelectionSummary, make_provider, select_candidate
from harness.models import Fact
from harness.reporting import report
from harness.runner import ingest, sweep
from harness.storage import Storage, write_json
from harness.summarize import summarize


def control(config, long=False):
    timeout = config.timeouts.control_seconds
    if long:
        timeout = (
            len(load_domains().all())
            * 2
            * config.measurement.attempts_per_domain
            * (config.timeouts.exit_probe_seconds + 2)
            + 30
        )
    return Control(timeout=timeout)


def remaining_window(config, now=None):
    now = now or datetime.now(UTC)
    start = now.replace(hour=config.schedule.start_hour_utc, minute=0, second=0, microsecond=0)
    if now < start:
        start -= timedelta(days=1)
    return max(
        0, int((start + timedelta(hours=config.schedule.window_hours) - now).total_seconds())
    )


def resolve_run(root, run_id):
    if run_id:
        return str(uuid.UUID(run_id))
    path = Path(root) / "state" / "last_run.json"
    if not path.exists():
        raise ValueError("provide --run-id; no completed run recorded")
    return str(uuid.UUID(json.loads(path.read_text())["run_id"]))


def run_sweep(config):
    duration = remaining_window(config)
    if not duration:
        raise ValueError("outside configured sweep window")
    run_id = sweep(
        control(config), load_domains().all(), config.data_dir, duration=min(duration, 21600)
    )
    write_json(Path(config.data_dir) / "state" / "last_run.json", {"run_id": run_id})
    return run_id


def analyze(config, run_id):
    store = Storage(config.data_dir)
    metadata = json.loads((store.root / "raw" / f"{run_id}.json").read_text())
    if metadata["status"] == "failed":
        raise ValueError("measurement failed; refusing downstream analysis")
    ingest(config.data_dir, run_id)
    facts = store.facts()
    current = [f for f in facts if f.run_id == run_id]
    try:
        health = control(config).call("client_health")
        routes = health.get("route", [])
        client = (
            health.get("available")
            and len(routes) == 1
            and routes[0].get("gateway") == "172.31.0.2"
        )
    except Exception:
        client = None
    invariants = evaluate_invariants(
        current,
        bypass_disabled=metadata.get("bypass_disabled"),
        overlap_harmed=False,
        client_available=client,
        min_addresses=config.measurement.min_distinct_addresses,
    )
    gates = evaluate_gates(facts, load_domains(), config)
    summary = summarize(run_id, facts, gates, invariants)
    summary["topology_scope"] = "Docker lab has one bypass branch and no tunnel branch"
    write_json(store.root / "summaries" / f"{run_id}.json", summary)
    write_json(store.root / "summaries" / "summary.json", summary["llm_input"])
    return summary


def llm(config, run_id):
    summary = analyze(config, run_id)
    result = select_candidate(
        SelectionSummary.model_validate(summary["llm_input"]), make_provider(config.llm), config.llm
    )
    output = {
        "run_id": run_id,
        **result.as_dict(),
        "eligible_candidates": [g for g in summary["gates"] if g["eligible"]],
    }
    write_json(Path(config.data_dir) / "state" / "selection.json", output)
    return output


def recheck(config, source_run):
    summary = analyze(config, source_run)
    candidates = [
        g for g in summary["gates"] if g["clean_wins"] and "has_failure" not in g["reasons"]
    ]
    returned, missing, ids = [], [], []
    for class_name in sorted({g["class_name"] for g in candidates}):
        strategies = sorted({g["strategy"] for g in candidates if g["class_name"] == class_name})[
            :10
        ]
        run_id, api = str(uuid.uuid4()), control(config)
        api.call("recheck", {"run_id": run_id, "class_name": class_name, "strategies": strategies})
        deadline = time.monotonic() + 21600
        while time.monotonic() < deadline:
            status = api.call("run_status", {"run_id": run_id})
            if status["status"] in {"completed", "failed"}:
                result = api.call("run_result", {"run_id": run_id})
                store = Storage(config.data_dir)
                facts = [Fact.model_validate_json(line) for line in result["recheck"].splitlines()]
                (store.root / "raw" / f"{run_id}.recheck.jsonl").write_text(result["recheck"])
                store.ingest(facts)
                missing.extend(result["missing"])
                returned.extend(f.strategy for f in facts)
                ids.append(run_id)
                break
            time.sleep(1)
        else:
            missing.extend(strategies)
    output = {"run_ids": ids, "returned": sorted(set(returned)), "missing": sorted(set(missing))}
    write_json(Path(config.data_dir) / "state" / "recheck.json", output)
    return output


def deploy(config, recheck_run):
    path = Path(config.data_dir) / "state" / "selection.json"
    selection = json.loads(path.read_text())
    response = selection.get("response")
    if not response or response["abstain"]:
        raise ValueError("no selected candidate")
    candidate = selection["eligible_candidates"][response["candidate_index"]]
    fresh = evaluate_gates(Storage(config.data_dir).facts(), load_domains(), config)
    if not any(
        g.eligible
        and g.strategy == candidate["strategy"]
        and g.class_name == candidate["class_name"]
        for g in fresh
    ):
        raise ValueError("candidate no longer eligible")
    result = control(config, long=True).call(
        "apply_strategy",
        {
            "run_id": str(uuid.UUID(recheck_run)),
            "strategy": candidate["strategy"],
            "class_name": candidate["class_name"],
        },
    )
    if result["status"] == "observing":
        write_json(
            Path(config.data_dir) / "state" / "expected.json", {"strategy": candidate["strategy"]}
        )
    return result


def pipeline(config, existing_run=None):
    store = Storage(config.data_dir)
    run_id = existing_run or run_sweep(config)
    try:
        summary = analyze(config, run_id)
        decision = llm(config, run_id)
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": summary,
            "llm": decision,
            "deployment": "NOT_REQUESTED",
            "watchdog": "NOT_REQUESTED",
            "rollback": "NOT_REQUESTED",
        }
    except Exception as exc:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "error": type(exc).__name__,
            "downstream": "STOPPED",
        }
        report(store.root, run_id, payload)
        raise
    return report(store.root, run_id, payload)
