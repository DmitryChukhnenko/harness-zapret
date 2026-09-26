"""Acceptance report derives every simulated verdict from executed pytest results."""

import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from harness.reporting import report
from harness.storage import Storage

CASES = {
    "П-1": ["test_idempotency_and_conflict_transaction"],
    "П-2": ["test_dates_are_not_runs"],
    "П-3": ["test_missing_recheck_and_loud_delivery"],
    "П-4": ["test_completed_probe_and_tail", "test_argument_roundtrip"],
    "П-5": [
        "test_watchdog_all_branches",
        "test_deploy_backup_restore",
        "test_start_failure_immediate_rollback",
    ],
    "П-6": ["test_overlap_rejected_then_released"],
    "П-7": ["test_client_unavailable", "test_watchdog_all_branches"],
    "П-8": ["test_harm_and_unknown"],
    "П-9": [
        "test_retry_exact_invalid_response_once",
        "test_abstain",
        "test_invalid_twice_stops",
        "test_annotation_and_abstention",
        "test_patch_is_exact_draft_and_refuses_hallucination",
        "test_loss_priority_and_unknown_abstain",
        "test_grid_hallucinations_and_duplicates_rejected",
    ],
    "П-10": ["test_missing_recheck_and_loud_delivery", "test_successful_report_sink"],
    "П-11": ["test_reconcile_both_nodes"],
    "П-12": ["test_each_deployment_refusal"],
}


def acceptance(root):
    root = Storage(root).root
    label = "acceptance-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    xml = root / "reports" / f"{label}.xml"
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-m", "not live", "-q", f"--junitxml={xml}"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    (root / "reports" / f"{label}.log").write_text(
        process.stdout + process.stderr, encoding="utf-8"
    )
    results = {}
    if xml.exists():
        for case in ET.parse(xml).iter("testcase"):
            results[case.attrib["name"]] = not any(
                case.find(tag) is not None for tag in ("error", "failure", "skipped")
            )
    cases = [
        {
            "id": name,
            "status": "PASS_SIMULATED" if all(results.get(t, False) for t in tests) else "FAIL",
            "tests": tests,
            "live_status": "SKIPPED_ENVIRONMENT",
            "live_reason": "Requires an enabled Linux lab; see docs/LIVE-VERIFICATION.md",
        }
        for name, tests in CASES.items()
    ]
    return report(
        root,
        label,
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "PASS_SIMULATED"
            if process.returncode == 0 and all(c["status"] == "PASS_SIMULATED" for c in cases)
            else "FAIL",
            "tests": len(results),
            "passed": sum(results.values()),
            "cases": cases,
        },
    )
