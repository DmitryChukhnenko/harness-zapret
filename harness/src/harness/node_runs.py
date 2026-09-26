import json
import os
import signal
import subprocess
import threading
import uuid
from pathlib import Path

from pydantic import Field, field_validator

from harness.config import Domains, StrictModel, load_config
from harness.locking import lock
from harness.storage import write_json

ROOT = Path("/state/runs")


class RunRef(StrictModel):
    run_id: str

    @field_validator("run_id")
    @classmethod
    def identifier(cls, value):
        return str(uuid.UUID(value))


class SweepRequest(RunRef):
    domains: list[str]
    duration: int = Field(default=3600, ge=1, le=21600)

    @field_validator("domains")
    @classmethod
    def names(cls, value):
        return Domains(classes={"sweep": value}).all()


def run(request):
    directory = ROOT / request.run_id
    directory.mkdir(parents=True, exist_ok=False)
    config = load_config()
    env = os.environ | {
        "BATCH": "1",
        "DOMAINS": " ".join(request.domains),
        "IPVS": "4",
        "REPEATS": str(config.measurement.attempts_per_domain),
        "PARALLEL": "0",
        "SCANLEVEL": "force",
        "SKIP_IPBLOCK": "1",
        "ENABLE_HTTP": "0",
        "ENABLE_HTTPS_TLS12": "1",
        "ENABLE_HTTPS_TLS13": "0",
        "ENABLE_HTTP3": "0",
        "HARNESS_EVENTS": str(directory / "events.jsonl"),
        "CURL_MAX_TIME": str(config.timeouts.exit_probe_seconds),
    }
    # Serialize with deployment/recheck. Invalid arguments have already been rejected.
    try:
        with lock("/state/operation.lock"):
            from harness.node_service import live_strategy

            if live_strategy():
                raise ValueError(
                    "sweep requires bypass disabled; use selective recheck when active"
                )
            write_json(directory / "status.json", {"status": "running", "bypass_disabled": True})
            with (directory / "raw.log").open("w", encoding="utf-8") as output:
                proc = subprocess.Popen(
                    ["sh", "/opt/zapret2/blockcheck2.sh"],
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                    cwd="/opt/zapret2",
                )
                try:
                    code = proc.wait(timeout=request.duration)
                    status = "completed" if code == 0 else "failed"
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    status = "timed_out"
            write_json(directory / "status.json", {"status": status, "bypass_disabled": True})
    except Exception:
        write_json(directory / "status.json", {"status": "failed", "bypass_disabled": False})


def dispatch(verb, payload):
    if verb == "run_blockcheck":
        request = SweepRequest.model_validate(payload)
        if (ROOT / request.run_id).exists():
            raise ValueError("run already exists")
        threading.Thread(target=run, args=(request,), daemon=True).start()
        return {"run_id": request.run_id}
    request = RunRef.model_validate(payload)
    directory = ROOT / request.run_id
    if verb == "run_status":
        path = directory / "status.json"
        return json.loads(path.read_text()) if path.exists() else {"status": "starting"}

    def read(name):
        path = directory / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    status = json.loads((directory / "status.json").read_text())
    if status["status"] == "running":
        raise ValueError("run is still active")
    return {
        "log": read("raw.log"),
        "events": read("events.jsonl"),
        "recheck": read("recheck.jsonl"),
        **status,
    }
