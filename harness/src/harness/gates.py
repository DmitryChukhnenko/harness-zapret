from collections import defaultdict

from harness.clean_win import clean_win
from harness.models import GateResult


def evaluate_gates(facts, domains, config):
    results = []
    for class_name, members in domains.classes.items():
        groups = defaultdict(list)
        for fact in facts:
            if fact.domain in members and fact.record_type == "probe":
                groups[(fact.strategy, fact.protocol, fact.address_family)].append(fact)
        for (strategy, protocol, family), probes in sorted(groups.items()):
            wins = [f for f in probes if clean_win(f, config.measurement.min_distinct_addresses)[0]]
            covered = sorted({f.domain for f in wins})
            runs = {f.run_id for f in wins}
            dates = {(f.run_timestamp or f.timestamp).date() for f in wins}
            reasons = []
            if not wins:
                reasons.append("no_clean_win")
            if set(members) - set(covered):
                reasons.append("missing_domain_coverage")
            if len(runs) < config.gates.min_runs:
                reasons.append("pending_more_runs")
            if len(dates) < config.gates.min_dates:
                reasons.append("pending_more_dates")
            if any(
                f.verdict == "BLOCKED_OR_FAILED"
                or (f.verdict == "OPEN" and f.success_count < f.attempt_count)
                for f in probes
            ):
                reasons.append("has_failure")
            results.append(
                GateResult(
                    class_name=class_name,
                    strategy=strategy,
                    protocol=protocol,
                    address_family=family,
                    eligible=not reasons,
                    reasons=reasons,
                    clean_wins=len(wins),
                    runs=len(runs),
                    dates=len(dates),
                    domains=covered,
                )
            )
    return results
