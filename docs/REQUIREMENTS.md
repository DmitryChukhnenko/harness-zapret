# Requirement traceability

Every numbered SPEC requirement is listed below. Paths to Python modules are
relative to `harness/src/harness/`; test names refer to `tests/` subdirectories.
`simulated` means the deterministic contract was exercised with controlled fixtures.
Live evidence is separate: [2026-09-29 results](evidence/live-20260929.json).

| Requirement | Implementation | Tests/evidence | Status |
|---|---|---|---|
| Т-3.1 | docker-compose.yml; node_runtime.py | test_deployment.py; live_control_check.py | live lab verified |
| Т-3.2 | docker-compose.yml; node_runtime.py | test_deployment.py; live_control_check.py | live lab verified |
| Т-3.3 | docker-compose.yml; node_runtime.py | test_deployment.py; live_control_check.py | live lab verified |
| Т-4.1 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-4.2 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-4.3 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-4.4 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-4.5 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-4.6 | models.py; parser.py; storage.py; runner.py | test_facts_gates.py; test_parser.py; test_recovery.py | implemented / simulated |
| Т-5.1 | trace.py; clean_win.py; invariants.py | test_facts_gates.py; test_parser.py | implemented / simulated |
| Т-5.2 | trace.py; clean_win.py; invariants.py | test_facts_gates.py; test_parser.py | implemented / simulated |
| Т-5.3 | trace.py; clean_win.py; invariants.py | test_facts_gates.py; test_parser.py | implemented / simulated |
| Т-5.4 | trace.py; clean_win.py; invariants.py | test_facts_gates.py; test_parser.py | implemented / simulated |
| Т-5.5 | trace.py; clean_win.py; invariants.py | test_facts_gates.py; test_parser.py | implemented / simulated |
| Т-6.1 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.2 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.3 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.4 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.5 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.6 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-6.7 | gates.py; node_runtime.py | test_facts_gates.py; test_recovery.py | implemented / simulated |
| Т-7.1 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-7.2 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-7.3 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-7.4 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-7.5 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-7.6 | probe.py; node.py; docker-compose.yml | test_probe_strategy.py; test_live.py | live topology and dual-point probes verified |
| Т-8.1 | recheck.py; node_runtime.py; node_service.py | test_deployment.py | live NFQUEUE recheck and lease recovery verified |
| Т-8.2 | recheck.py; node_runtime.py; node_service.py | test_deployment.py | live NFQUEUE recheck and lease recovery verified |
| Т-8.3 | recheck.py; node_runtime.py; node_service.py | test_deployment.py | live NFQUEUE recheck and lease recovery verified |
| Т-9.1 | strategy.py; trace.py; node_service.py | test_probe_strategy.py; test_contracts.py | implemented / simulated |
| Т-9.2 | strategy.py; trace.py; node_service.py | test_probe_strategy.py; test_contracts.py | implemented / simulated |
| Т-9.3 | strategy.py; trace.py; node_service.py | test_probe_strategy.py; test_contracts.py | implemented / simulated |
| Т-10.1 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.2 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.3 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.4 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.5 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.6 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.7 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.8 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.9 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.10 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-10.11 | deployment.py; watchdog.py; node_runtime.py | test_deployment.py; test_invariants_watchdog.py | live controlled-lab lifecycle verified; fixture admission, shortened windows |
| Т-11.1 | invariants.py; summarize.py | test_invariants_watchdog.py | implemented / simulated; single-branch lab scope |
| Т-11.2 | invariants.py; summarize.py | test_invariants_watchdog.py | implemented / simulated; single-branch lab scope |
| Т-11.3 | invariants.py; summarize.py | test_invariants_watchdog.py | implemented / simulated; single-branch lab scope |
| Т-11.4 | invariants.py; summarize.py | test_invariants_watchdog.py | implemented / simulated; single-branch lab scope |
| Т-12.1 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.2 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.3 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.4 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.5 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.6 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented: typed library APIs for five lanes; selection exposed in main CLI |
| Т-12.7 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-12.8 | llm.py; llm_tasks.py | test_llm.py; test_llm_tasks.py | implemented: structured option/value proposals; assembled and validated locally |
| Т-13.1 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-13.2 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-13.3 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-13.4 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-13.5 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-13.6 | llm.py; control.py; node.py; strategy.py | test_llm.py; test_config.py | implemented / simulated |
| Т-14.1 | budget.py; node_budget.py | test_budget.py | implemented / simulated; live module filtering pending |
| Т-14.2 | budget.py; node_budget.py | test_budget.py | implemented / simulated; live module filtering pending |
| Т-14.3 | budget.py; node_budget.py | test_budget.py | implemented / simulated; live module filtering pending |
| Т-14.4 | budget.py; node_budget.py | test_budget.py | implemented / simulated; live module filtering pending |
| Т-15.1 | reconcile.py; pipeline.py | test_contracts.py; live_control_check.py | live two-node drift verified |
| Т-15.2 | reconcile.py; pipeline.py | test_contracts.py; live_control_check.py | live two-node drift verified |
| Т-15.3 | reconcile.py; pipeline.py | test_contracts.py; live_control_check.py | live two-node drift verified |
| Т-15.4 | reconcile.py; pipeline.py | test_contracts.py; live_control_check.py | live two-node drift verified |
| Т-16.1 | reporting.py; node_runtime.py; probe.py | test_deployment.py; test_contracts.py | not configured: external ReportSink interface exists; local sink only |
| Т-16.2 | reporting.py; node_runtime.py; probe.py | test_deployment.py; test_contracts.py | implemented / simulated |
| Т-16.3 | reporting.py; node_runtime.py; probe.py | test_deployment.py; test_contracts.py | implemented / simulated |
| Т-16.4 | reporting.py; node_runtime.py; probe.py | test_deployment.py; test_contracts.py | implemented / simulated |
| Т-16.5 | reporting.py; node_runtime.py; probe.py | test_deployment.py; test_contracts.py | implemented / simulated |
| Т-17.1 | pipeline.py; node_runs.py; locking.py | test_pipeline.py; test_recovery.py; test_invariants_watchdog.py | implemented / simulated |
| Т-17.2 | pipeline.py; node_runs.py; locking.py | test_pipeline.py; test_recovery.py; test_invariants_watchdog.py | implemented / simulated |
| Т-17.3 | pipeline.py; node_runs.py; locking.py | test_pipeline.py; test_recovery.py; test_invariants_watchdog.py | implemented / simulated |
| Т-17.4 | pipeline.py; node_runs.py; locking.py | test_pipeline.py; test_recovery.py; test_invariants_watchdog.py | implemented / simulated |
| Т-18.1 | llm.py; llm_tasks.py; evaluation.py | test_llm.py; test_llm_tasks.py | implemented / simulated; paid evaluation opt-in |
| Т-18.2 | llm.py; llm_tasks.py; evaluation.py | test_llm.py; test_llm_tasks.py | implemented / simulated; paid evaluation opt-in |
| Т-18.3 | llm.py; llm_tasks.py; evaluation.py | test_llm.py; test_llm_tasks.py | implemented / simulated; paid evaluation opt-in |
| Т-18.4 | llm.py; llm_tasks.py; evaluation.py | test_llm.py; test_llm_tasks.py | implemented / simulated; paid evaluation opt-in |
| Т-18.5 | llm.py; llm_tasks.py; evaluation.py | test_llm.py; test_llm_tasks.py | implemented / simulated; paid evaluation opt-in |
| Т-19.1 | docker-compose.yml; llm.py; cli.py | test_llm.py; test_live.py | architecture override: Python in Docker measurement node; embedded target excluded |
| Т-19.2 | docker-compose.yml; llm.py; cli.py | test_llm.py; test_live.py | architecture override: Docker named volumes and host data directory |
| Т-19.3 | docker-compose.yml; llm.py; cli.py | test_llm.py; test_live.py | Docker architecture override / environment-dependent |
| Т-19.4 | docker-compose.yml; llm.py; cli.py | test_llm.py; test_live.py | partial: measured tokens; billed cost unavailable from completion response |
| Т-19.5 | docker-compose.yml; llm.py; cli.py | test_llm.py; test_live.py | Docker architecture override / environment-dependent |
| Т-20.1 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-20.2 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-20.3 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-20.4 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-20.5 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |
| Т-20.6 | deployment.py; node_runtime.py; llm.py; llm_tasks.py | test_deployment.py; test_llm.py; test_llm_tasks.py | implemented / simulated |

## Acceptance criteria

Authoritative per-run verdicts/counts are in `data/reports/acceptance-*.json`.
The executable mapping is `harness/acceptance.py`; missing tests produce FAIL.

| Criterion | Executed fixtures | Verification status |
|---|---|---|
| П-1 | test_idempotency_and_conflict_transaction | PASS_SIMULATED; live not measured |
| П-2 | test_dates_are_not_runs | PASS_SIMULATED; live not measured |
| П-3 | test_missing_recheck_and_loud_delivery | PASS_SIMULATED; live not measured |
| П-4 | test_completed_probe_and_tail; test_argument_roundtrip | PASS_SIMULATED; PASS_LIVE: upstream argv roundtrip |
| П-5 | test_watchdog_all_branches; test_deploy_backup_restore; test_start_failure_immediate_rollback | PASS_SIMULATED; PASS_LIVE: controlled lab; admission fixture, shortened windows |
| П-6 | test_overlap_rejected_then_released | PASS_SIMULATED; PASS_LIVE: Linux lock contention/release |
| П-7 | test_client_unavailable; test_watchdog_all_branches | PASS_SIMULATED; PASS_LIVE: real client control firewall fault |
| П-8 | test_harm_and_unknown | PASS_SIMULATED; live not measured |
| П-9 | test_retry_exact_invalid_response_once; test_abstain; test_invalid_twice_stops; test_annotation_and_abstention; test_patch_is_exact_draft_and_refuses_hallucination; test_loss_priority_and_unknown_abstain; test_grid_hallucinations_and_duplicates_rejected | PASS_SIMULATED; live not measured |
| П-10 | test_missing_recheck_and_loud_delivery; test_successful_report_sink | PASS_SIMULATED; NOT_CONFIGURED: external recipient required |
| П-11 | test_reconcile_both_nodes | PASS_SIMULATED; PASS_LIVE: external strategy and client route drift |
| П-12 | test_each_deployment_refusal | PASS_SIMULATED; PASS_LIVE: real engine refusals in isolated lab |

## Outstanding live evidence

Docker images, transit routing, NFQUEUE, selective recheck, lease recovery and
rollback were measured on 2026-09-29, including with Harness stopped. See
[LIVE-VERIFICATION.md](LIVE-VERIFICATION.md) for scope, commands and limitations.
Actual two-date qualification and full-night module allocation remain unmeasured.
External report delivery is not configured.
No paid Mistral request was made; the official HTTP contract was verified offline.
