from harness.clean_win import clean_win
from harness.models import Invariant


def evaluate_invariants(
    facts, *, bypass_disabled=None, overlap_harmed=None, client_available=None, min_addresses=2
):
    probes = [f for f in facts if f.record_type == "probe"]
    ambiguous = (
        any(f.record_type == "baseline" and f.verdict == "OPEN" for f in facts) and not probes
    )
    thin = sum(
        clean_win(f, min_addresses)[1]
        in {"no_recorded_addresses", "insufficient_distinct_addresses"}
        for f in probes
        if f.verdict == "OPEN"
    )
    shaky = sum(f.verdict == "OPEN" and f.success_count < f.attempt_count for f in probes)

    def measured(name, value, reason):
        return Invariant(
            name=name,
            status="UNKNOWN" if value is None else "PASS" if value else "FAIL",
            reason=reason,
        )

    return [
        measured("measurement_integrity", bypass_disabled, "sweep bypass-disabled evidence"),
        measured(
            "ambiguous_baseline",
            None if not facts else not ambiguous,
            "positive baseline with zero strategies is ambiguous",
        ),
        measured(
            "routing_overlap_harm",
            None if overlap_harmed is None else not overlap_harmed,
            "overlap alone is harmless; measured user-facing failure is required",
        ),
        measured(
            "win_quality", None if not probes else thin + shaky == 0, f"thin={thin}; shaky={shaky}"
        ),
        measured("client_available", client_available, "unavailable client is unmeasured"),
    ]
