"""Bounded curl probes preserve Host/SNI when a destination address is forced."""

import json
import socket
import subprocess
from ipaddress import ip_address
from typing import Literal

from pydantic import Field, model_validator

from harness.config import Domains, StrictModel


class ProbeRequest(StrictModel):
    domain: str
    address: str | None = None
    address_family: Literal[4, 6] = 4
    protocol: Literal["https_tls12", "https_tls13", "http"] = "https_tls12"
    attempts: int = Field(default=2, ge=2, le=20)
    timeout: int = Field(default=5, ge=1, le=60)

    @model_validator(mode="after")
    def valid_target(self):
        Domains(classes={"probe": [self.domain]})
        if self.address and ip_address(self.address).version != self.address_family:
            raise ValueError("destination address family mismatch")
        return self


def resolve(domain, family):
    af = socket.AF_INET if family == 4 else socket.AF_INET6
    return sorted({record[4][0] for record in socket.getaddrinfo(domain, None, af)})


def probe(request, execute=subprocess.run):
    request = ProbeRequest.model_validate(request) if isinstance(request, dict) else request
    args = [
        "curl",
        "--silent",
        "--show-error",
        "--noproxy",
        "*",
        "--output",
        "/dev/null",
        "--max-time",
        str(request.timeout),
        "--write-out",
        "%{json}",
        "--ipv4" if request.address_family == 4 else "--ipv6",
    ]
    scheme, port = ("http", 80) if request.protocol == "http" else ("https", 443)
    if request.protocol == "https_tls12":
        args += ["--tlsv1.2", "--tls-max", "1.2"]
    elif request.protocol == "https_tls13":
        args += ["--tlsv1.3", "--tls-max", "1.3"]
    if request.address:
        address = f"[{request.address}]" if request.address_family == 6 else request.address
        args += ["--resolve", f"{request.domain}:{port}:{address}"]
    args.append(f"{scheme}://{request.domain}/")
    outcomes, addresses = [], []
    for _ in range(request.attempts):
        try:
            response = execute(
                args, capture_output=True, text=True, timeout=request.timeout + 1, check=False
            )
            body = json.loads(response.stdout or "{}")
            if body.get("remote_ip"):
                addresses.append(str(ip_address(body["remote_ip"])))
            code = body.get("http_code", 0)
            if request.address and code == 421:
                outcome = "ADDRESS_NOT_SERVING_HOST"
            elif response.returncode == 0 and 200 <= code < 400:
                outcome = "OPEN"
            else:
                outcome = "BLOCKED_OR_FAILED"
        except (OSError, subprocess.TimeoutExpired, ValueError):
            outcome = "UNMEASURED"
        outcomes.append(outcome)
    if all(x == "OPEN" for x in outcomes):
        verdict = "OPEN"
    elif "UNMEASURED" in outcomes:
        verdict = "UNMEASURED"
    elif "ADDRESS_NOT_SERVING_HOST" in outcomes:
        verdict = "ADDRESS_NOT_SERVING_HOST"
    else:
        verdict = "BLOCKED_OR_FAILED"
    return {
        "verdict": verdict,
        "success_count": outcomes.count("OPEN"),
        "attempt_count": request.attempts,
        "frontend_addresses": sorted(set(addresses)),
    }


def remote_probe(control, request):
    try:
        return control.call("probe", request.model_dump())
    except Exception:
        return {
            "verdict": "UNMEASURED",
            "success_count": 0,
            "attempt_count": request.attempts,
            "frontend_addresses": [],
        }
