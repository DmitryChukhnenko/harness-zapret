"""Measurement node service; all externally supplied arguments use strict schemas."""

import hmac
import json
import os
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from harness.config import StrictModel


def command(args, timeout=5):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def health(point):
    if point == "client":
        route = command(["ip", "-j", "route", "show", "default"])
        return {"point": point, "route": json.loads(route.stdout), "available": True}
    firewall = command(["nft", "list", "tables"])
    version = command(["/opt/zapret2/nfq2/nfqws2", "--version"])
    return {
        "point": point,
        "available": firewall.returncode == 0,
        "firewall": firewall.returncode == 0,
        "revision": Path("/opt/zapret2/REVISION").read_text().strip(),
        "nfqws": version.returncode == 0,
        "blockcheck": Path("/opt/zapret2/blockcheck2.sh").is_file(),
    }


def dispatch(point, verb, payload):
    if point == "gateway" and verb == "path_probe":
        StrictModel.model_validate(payload)
        from harness.config import load_config, load_domains
        from harness.node_runtime import client_control
        from harness.probe import ProbeRequest, remote_probe

        def packets():
            output = command(
                ["nft", "-j", "list", "counter", "inet", "harness_path", "client_forward"]
            )
            if output.returncode:
                raise ValueError("forwarding counter unavailable")
            return next(
                row["counter"]["packets"]
                for row in json.loads(output.stdout)["nftables"]
                if "counter" in row
            )

        before = packets()
        config = load_config()
        outcome = remote_probe(
            client_control(),
            ProbeRequest(
                domain=load_domains().all()[0],
                attempts=config.measurement.attempts_per_domain,
                timeout=config.timeouts.exit_probe_seconds,
            ),
        )
        delta = packets() - before
        return {
            "status": "PASS" if delta > 0 and outcome["verdict"] != "UNMEASURED" else "UNKNOWN",
            "forwarded_packets": delta,
            "probe_verdict": outcome["verdict"],
        }
    if point == "gateway" and verb in {"apply_strategy", "recheck"}:
        from harness.node_runtime import apply, recheck

        return apply(payload) if verb == "apply_strategy" else recheck(payload)
    if point == "gateway" and verb in {
        "get_config",
        "service_status",
        "watchdog",
        "restore_backup",
    }:
        StrictModel.model_validate(payload)
        from harness.node_runtime import engine
        from harness.node_service import live_strategy, service_status

        if verb == "get_config":
            return {"strategy": live_strategy(), "deployment": engine().state()}
        if verb == "service_status":
            return {"running": service_status()}
        return engine().watchdog() if verb == "watchdog" else engine().rollback()
    if verb == "probe":
        from harness.probe import ProbeRequest, probe

        request = ProbeRequest.model_validate(payload)
        return probe(request)
    if point == "gateway" and verb == "client_health":
        StrictModel.model_validate(payload)
        from harness.control import Control

        return Control(endpoint="http://172.31.0.3:8080").call("health")
    if point == "gateway" and verb in {"run_blockcheck", "run_status", "run_result"}:
        from harness.node_runs import dispatch as dispatch_run

        return dispatch_run(verb, payload)
    if verb == "health":
        StrictModel.model_validate(payload)
        return health(point)
    raise ValueError("unsupported control operation")


def serve(point):
    if point == "gateway":
        from harness.node_runtime import startup

        startup()
    token = Path("/auth/token").read_text().strip()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Never write authorization or request data.

        def do_POST(self):
            if not hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}"):
                self.send_error(401)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("invalid payload size")
                self.connection.settimeout(5)
                result = dispatch(point, self.path.lstrip("/"), json.loads(self.rfile.read(length)))
                body, status = json.dumps(result).encode(), 200
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
                body, status = b'{"error":"operation refused or unavailable"}', 400
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    address = "172.30.0.2" if point == "gateway" else "172.31.0.3"
    ThreadingHTTPServer((address, 8080), Handler).serve_forever()


def main():
    if sys.argv[1] == "init":
        path = Path("/auth/token")
        if not path.exists():
            path.write_text(secrets.token_urlsafe(32))
            os.chmod(path, 0o600)
    elif sys.argv[1] == "healthcheck":
        from harness.control import Control

        sys.exit(0 if Control().call("health")["available"] else 1)
    else:
        serve(sys.argv[2])


if __name__ == "__main__":
    main()
