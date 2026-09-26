from datetime import UTC, datetime

from harness.models import Fact
from harness.probe import ProbeRequest, probe, remote_probe, resolve


def missing_rechecks(sent, returned):
    return sorted(set(sent) - set(returned))


def measure_candidate(run_id, strategy, domains, client, config, start_sequence=0):
    facts = []
    for domain in domains:
        try:
            addresses = resolve(domain, 4)
        except OSError:
            addresses = []
        for point in ("gateway", "client"):
            outcomes = []
            for address in addresses[: config.measurement.min_distinct_addresses]:
                request = ProbeRequest(
                    domain=domain,
                    address=address,
                    attempts=config.measurement.attempts_per_domain,
                    timeout=config.timeouts.exit_probe_seconds,
                )
                outcomes.append(
                    probe(request) if point == "gateway" else remote_probe(client, request)
                )
            if not outcomes or any(o["verdict"] == "UNMEASURED" for o in outcomes):
                verdict = "UNMEASURED"
            elif any(o["verdict"] == "ADDRESS_NOT_SERVING_HOST" for o in outcomes):
                verdict = "ADDRESS_NOT_SERVING_HOST"
            elif all(o["verdict"] == "OPEN" for o in outcomes):
                verdict = "OPEN"
            else:
                verdict = "BLOCKED_OR_FAILED"
            facts.append(
                Fact(
                    run_id=run_id,
                    timestamp=datetime.now(UTC),
                    sequence=start_sequence + len(facts),
                    record_type="probe",
                    domain=domain,
                    address_family=4,
                    protocol="https_tls12",
                    source="recheck",
                    strategy=strategy,
                    verdict=verdict,
                    success_count=sum(o["success_count"] for o in outcomes),
                    attempt_count=sum(o["attempt_count"] for o in outcomes)
                    or config.measurement.attempts_per_domain,
                    frontend_addresses=sorted(
                        {a for o in outcomes for a in o["frontend_addresses"]}
                    ),
                    measurement_point=point,
                )
            )
    return facts
