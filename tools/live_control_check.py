"""Host-side opt-in checks: external drift detection and failure-domain isolation.

Run with the project venv from the project root. Only this Compose project's
containers are modified, with configuration/routes/services restored in finally.
"""

import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from harness.config import load_domains
from harness.storage import write_json


def docker(*args, check=True, timeout=150):
    result = subprocess.run(
        ["docker", "compose", *args], capture_output=True, text=True, timeout=timeout
    )
    if check and result.returncode:
        raise RuntimeError(f"Docker command failed: {args[0]} (exit {result.returncode})")
    return result


def python(service, code):
    return docker("exec", "-T", service, "python", "-c", code).stdout


def reconcile(*args):
    return json.loads(docker("exec", "-T", "harness", "harness", "reconcile", *args).stdout)


def wait_gateway():
    for _ in range(35):
        result = docker(
            "exec", "-T", "zapret", "python", "-m", "harness.node", "healthcheck", check=False
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("gateway did not recover")


def main():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        raise RuntimeError("set HARNESS_LIVE_TESTS=1 for this isolated lab diagnostic")
    evidence = {"timestamp": datetime.now(UTC).isoformat(), "status": "FAIL"}
    out = Path("data/reports/control-live.json")
    snapshot = json.loads(
        python(
            "zapret",
            "import json; from pathlib import Path; p=Path('/state/strategy.conf'); "
            "print(json.dumps({'exists':p.exists(),'text':p.read_text() if p.exists() else ''}))",
        )
    )
    if snapshot["text"].strip():
        raise RuntimeError("requires empty live strategy")
    try:
        evidence["initial"] = reconcile("--initialize")
        assert evidence["initial"]["status"] == "PASS"
        python(
            "zapret",
            "from pathlib import Path; "
            "Path('/state/strategy.conf').write_text('--payload=tls_client_hello\\n')",
        )
        evidence["strategy_drift"] = reconcile()
        assert evidence["strategy_drift"]["status"] == "DRIFT"
    finally:
        if snapshot["exists"]:
            python(
                "zapret",
                "from pathlib import Path; Path('/state/strategy.conf').write_text("
                + repr(snapshot["text"])
                + ")",
            )
        else:
            python("zapret", "from pathlib import Path; Path('/state/strategy.conf').unlink()")

    try:
        docker("exec", "-T", "client", "ip", "route", "replace", "default", "via", "172.31.0.254")
        evidence["client_route_drift"] = reconcile()
        assert evidence["client_route_drift"]["status"] == "DRIFT"
    finally:
        docker("exec", "-T", "client", "ip", "route", "replace", "default", "via", "172.31.0.2")
    domain = load_domains().all()[0]
    address = python("client", f"import socket; print(socket.gethostbyname({domain!r}))").strip()
    try:
        docker("stop", "zapret")
        result = docker(
            "exec",
            "-T",
            "client",
            "curl",
            "--noproxy",
            "*",
            "-4",
            "--silent",
            "--max-time",
            "3",
            "--resolve",
            f"{domain}:443:{address}",
            f"https://{domain}/",
            check=False,
        )
        assert result.returncode != 0
        evidence["gateway_stopped_client_cannot_bypass"] = {"curl_exit": result.returncode}
    finally:
        docker("start", "zapret")
        wait_gateway()

    try:
        docker("stop", "harness")
        result = docker(
            "exec", "-T", "-e", "HARNESS_LIVE_TESTS=1", "zapret", "python", "/app/live_lifecycle.py"
        )
        lifecycle = json.loads(result.stdout)
        assert lifecycle["status"] == "PASS_LIVE"
        evidence["lifecycle_with_harness_stopped"] = lifecycle["path"]
    finally:
        docker("start", "harness")
    evidence["restored"] = reconcile()
    assert evidence["restored"]["status"] == "PASS"
    evidence["status"] = "PASS_LIVE"
    write_json(out, evidence)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
