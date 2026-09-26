# Current state

## Last completed phase
Phases 0–1 committed; Compose config and upstream instrumentation validated.

## Current phase
Phases 5–11 implemented; integration hardening and acceptance/finalization next.

## Completed
- Read the attached implementation brief and authoritative SPEC.md.
- Confirmed production provider: Mistral, mistral-small-latest,
  https://api.mistral.ai/v1/chat/completions, JSON Schema structured outputs.
- Created local Python environment and installed development dependencies.
- Compose validates; instrumenter anchors verified against pinned upstream source.
- Isolated management/lab networks, explicit client default route and gateway NAT.
- Authenticated finite control API, node health checks, CLI doctor.
- Bounded async blockcheck runs; raw stdout and trusted events archived separately.
- Typed facts, strict parser, interrupted-tail accounting, incremental/full ingestion.
- SQLite idempotency key (run_id, timestamp, sequence), conflict detection and JSONL export.
- Single clean-win definition, class gates with distinct run/date conditions.
- 11 unit tests pass; ruff passes. Docker build attempted: daemon unavailable.
- Gateway/client probes preserve Host/SNI for destination IP overrides; offline is UNMEASURED.
- Corpus-derived strategy operation validation and deployment safety checks.
- Provider protocol, MockProvider and official Mistral chat completions JSON Schema requests.
- Index-only selection, abstain, one schema retry, local validation, usage accounting.
- LLM credentials only MISTRAL_API_KEY; no configurable endpoint or credential field.
- 40 offline tests pass, including 20 Mistral/schema/error-path cases.
- Dual-point selective recheck with expiring exclusions and corpus-only candidates.
- Invariants, compact summaries and deterministic module budget calculations.
- Five LLM lanes: selection, annotation, patch draft, prioritized loss reason and bounded grid draft.
- Gateway-local deployment transaction, service validation, backup/rollback and watchdog thread.
- CLI stages, UTC sweep window, fresh ingestion before LLM, reports and reconciliation.
- 51 tests pass, including deployment refusal and immediate rollback branches; ruff passes.

## Remaining
- Phase 12: acceptance case mapping and reports, live checks with honest environment skips.
- Phase 13: operational hardening, README, requirements traceability and final verification.
- Verify shared DNS and transit topology; strengthen interrupted-run and recheck rebuild handling.

## Known issues
- Docker Desktop Linux daemon unavailable, including outside the sandbox.
  Live networking/build checks are not yet possible; no live pass is claimed.

## Verification commands
- `.venv/Scripts/python.exe -m pytest`
- `.venv/Scripts/python.exe -m ruff check .`
- `docker compose config --quiet`

## Important architectural decisions
- Separate harness, zapret and client containers; no privileged container.
- API credentials only through MISTRAL_API_KEY; tests use MockProvider.
- LLM receives a bounded typed summary and selects only an eligible index.
- Local watchdog and backups must survive loss of the harness.
