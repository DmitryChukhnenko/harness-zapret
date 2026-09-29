from collections import Counter

from harness.clean_win import clean_win
from harness.llm import Candidate, InvariantView, SelectionSummary


def summarize(run_id, facts, gates, invariants, min_addresses=2):
    current = [f for f in facts if f.run_id == run_id]
    eligible = [gate for gate in gates if gate.eligible]
    view = SelectionSummary(
        eligible_candidates=[
            Candidate(
                index=i,
                clean_wins=g.clean_wins,
                runs=g.runs,
                dates=g.dates,
                domain_count=len(g.domains),
            )
            for i, g in enumerate(eligible)
        ],
        invariants=[InvariantView(name=i.name, status=i.status) for i in invariants],
    )
    missing_addresses = sum(not f.frontend_addresses for f in current if f.record_type == "probe")
    return {
        "schema_version": 1,
        "run_id": run_id,
        "fact_count": len(current),
        "domains": sorted({f.domain for f in current}),
        "strategy_count": len({f.strategy for f in current if f.record_type == "probe"}),
        "measurement_points": {
            point: "MEASURED"
            if any(f.measurement_point == point and f.verdict != "UNMEASURED" for f in current)
            else "UNMEASURED"
            for point in ("gateway", "client")
        },
        "clean_wins": sum(clean_win(f, min_addresses)[0] for f in current),
        "missing_addresses": missing_addresses,
        "warnings": ["No addresses recorded: clean wins structurally zero for these probes"]
        if missing_addresses
        else [],
        "invariants": [i.model_dump() for i in invariants],
        "gates": [g.model_dump() for g in gates],
        "rejected_summary": dict(Counter(reason for g in gates for reason in g.reasons)),
        "llm_input": view.model_dump(),
    }
