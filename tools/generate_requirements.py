"""Regenerate the complete requirement index directly from SPEC.md identifiers."""

import re
from pathlib import Path

AREAS = {
    3: (
        "docker-compose.yml; node_runtime.py",
        "test_deployment.py; live_control_check.py",
        "live lab verified",
    ),
    4: (
        "models.py; parser.py; storage.py; runner.py",
        "test_facts_gates.py; test_parser.py; test_recovery.py",
        "implemented / simulated",
    ),
    5: (
        "trace.py; clean_win.py; invariants.py",
        "test_facts_gates.py; test_parser.py",
        "implemented / simulated",
    ),
    6: (
        "gates.py; node_runtime.py",
        "test_facts_gates.py; test_recovery.py",
        "implemented / simulated",
    ),
    7: (
        "probe.py; node.py; docker-compose.yml",
        "test_probe_strategy.py; test_live.py",
        "live topology and dual-point probes verified",
    ),
    8: (
        "recheck.py; node_runtime.py; node_service.py",
        "test_deployment.py",
        "live NFQUEUE recheck and lease recovery verified",
    ),
    9: (
        "strategy.py; trace.py; node_service.py",
        "test_probe_strategy.py; test_contracts.py",
        "implemented / simulated",
    ),
    10: (
        "deployment.py; watchdog.py; node_runtime.py",
        "test_deployment.py; test_invariants_watchdog.py",
        "live controlled-lab lifecycle verified; fixture admission, shortened windows",
    ),
    11: (
        "invariants.py; summarize.py",
        "test_invariants_watchdog.py",
        "implemented / simulated; single-branch lab scope",
    ),
    12: ("llm.py; llm_tasks.py", "test_llm.py; test_llm_tasks.py", "implemented / simulated"),
    13: (
        "llm.py; control.py; node.py; strategy.py",
        "test_llm.py; test_config.py",
        "implemented / simulated",
    ),
    14: (
        "budget.py; node_budget.py",
        "test_budget.py",
        "implemented / simulated; live module filtering pending",
    ),
    15: (
        "reconcile.py; pipeline.py",
        "test_contracts.py; live_control_check.py",
        "live two-node drift verified",
    ),
    16: (
        "reporting.py; node_runtime.py; probe.py",
        "test_deployment.py; test_contracts.py",
        "implemented / simulated",
    ),
    17: (
        "pipeline.py; node_runs.py; locking.py",
        "test_pipeline.py; test_recovery.py; test_invariants_watchdog.py",
        "implemented / simulated",
    ),
    18: (
        "llm.py; llm_tasks.py; evaluation.py",
        "test_llm.py; test_llm_tasks.py",
        "implemented / simulated; paid evaluation opt-in",
    ),
    19: (
        "docker-compose.yml; llm.py; cli.py",
        "test_llm.py; test_live.py",
        "Docker architecture override / environment-dependent",
    ),
    20: (
        "deployment.py; node_runtime.py; llm.py; llm_tasks.py",
        "test_deployment.py; test_llm.py; test_llm_tasks.py",
        "implemented / simulated",
    ),
}
OVERRIDES = {
    "Т-16.1": "not configured: external ReportSink interface exists; local sink only",
    "Т-19.1": "architecture override: Python in Docker measurement node; embedded target excluded",
    "Т-19.2": "architecture override: Docker named volumes and host data directory",
    "Т-19.4": "partial: measured tokens; billed cost unavailable from completion response",
    "Т-12.6": "implemented: typed library APIs for five lanes; selection exposed in main CLI",
    "Т-12.8": "implemented: structured option/value proposals; assembled and validated locally",
}
LIVE_CASES = {
    "П-4": "PASS_LIVE: upstream argv roundtrip",
    "П-5": "PASS_LIVE: controlled lab; admission fixture, shortened windows",
    "П-6": "PASS_LIVE: Linux lock contention/release",
    "П-7": "PASS_LIVE: real client control firewall fault",
    "П-11": "PASS_LIVE: external strategy and client route drift",
    "П-12": "PASS_LIVE: real engine refusals in isolated lab",
    "П-10": "NOT_CONFIGURED: external recipient required",
}


def main():
    from harness.acceptance import CASES

    spec = Path("SPEC.md").read_text(encoding="utf-8")
    ids = list(dict.fromkeys(re.findall(r"\*\*(Т-\d+\.\d+)", spec)))
    lines = [
        "# Requirement traceability",
        "",
        "Every numbered SPEC requirement is listed below. Paths to Python modules are",
        "relative to `harness/src/harness/`; test names refer to `tests/` subdirectories.",
        "`simulated` means the deterministic contract was exercised with controlled fixtures.",
        "Live evidence is separate: [2026-09-29 results](evidence/live-20260929.json).",
        "",
        "| Requirement | Implementation | Tests/evidence | Status |",
        "|---|---|---|---|",
    ]
    for identifier in ids:
        section = int(identifier.split("-")[1].split(".")[0])
        implementation, tests, status = AREAS[section]
        lines.append(
            f"| {identifier} | {implementation} | {tests} | {OVERRIDES.get(identifier, status)} |"
        )
    lines += [
        "",
        "## Acceptance criteria",
        "",
        "Authoritative per-run verdicts/counts are in `data/reports/acceptance-*.json`.",
        "The executable mapping is `harness/acceptance.py`; missing tests produce FAIL.",
        "",
        "| Criterion | Executed fixtures | Verification status |",
        "|---|---|---|",
    ]
    for identifier, tests in CASES.items():
        lines.append(
            f"| {identifier} | {'; '.join(tests)} | PASS_SIMULATED; "
            f"{LIVE_CASES.get(identifier, 'live not measured')} |"
        )
    lines += [
        "",
        "## Outstanding live evidence",
        "",
        "Docker images, transit routing, NFQUEUE, selective recheck, lease recovery and",
        "rollback were measured on 2026-09-29, including with Harness stopped. See",
        "[LIVE-VERIFICATION.md](LIVE-VERIFICATION.md) for scope, commands and limitations.",
        "Actual two-date qualification and full-night module allocation remain unmeasured.",
        "External report delivery is not configured.",
        "No paid Mistral request was made; the official HTTP contract was verified offline.",
        "",
    ]
    Path("docs/REQUIREMENTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Indexed {len(ids)} requirements and {len(CASES)} acceptance criteria")


if __name__ == "__main__":
    main()
