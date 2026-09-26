"""Parse trusted local event records, never infer facts from server-controlled text."""

import json
from dataclasses import dataclass
from datetime import datetime
from ipaddress import ip_address

from harness.models import Fact


@dataclass
class ParseResult:
    facts: list[Fact]
    discarded_tail: int = 0


def parse_events(text: str, run_id: str) -> ParseResult:
    result = ParseResult([])
    pending = None
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if not line.endswith("\n") and i == len(lines) - 1:
            result.discarded_tail += 1
            break
        event = json.loads(line)  # Corrupt completed records stop ingestion.
        op, args = event["event"], event["args"]
        if op == "begin":
            if pending is not None:
                raise ValueError("overlapping event probes")
            domain, protocol, family, strategy, source = args
            pending = dict(
                domain=domain,
                protocol=protocol.removeprefix("curl_test_"),
                address_family=int(family),
                strategy=strategy,
                source=source,
                timestamp=datetime.fromisoformat(event["timestamp"]),
                addresses=[],
                attempts=[],
            )
        elif pending is not None and op == "address":
            pending["addresses"].append(str(ip_address(args[0].strip("[]"))))
        elif pending is not None and op == "attempt":
            pending["attempts"].append(int(args[0]))
        elif pending is not None and op == "end":
            attempts = pending.pop("attempts")
            addresses = pending.pop("addresses")
            if not attempts:
                raise ValueError("completed probe without attempts")
            strategy = pending["strategy"]
            result.facts.append(
                Fact(
                    **pending,
                    run_id=run_id,
                    sequence=len(result.facts),
                    record_type="probe" if strategy else "baseline",
                    measurement_point="gateway",
                    frontend_addresses=sorted(set(addresses)),
                    verdict="OPEN" if int(args[0]) == 0 else "BLOCKED_OR_FAILED",
                    success_count=attempts.count(0),
                    attempt_count=len(attempts),
                )
            )
            pending = None
    if pending is not None:
        result.discarded_tail += 1
    return result
