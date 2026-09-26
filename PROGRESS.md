# Current state

## Last completed phase
Phases 0–1 committed; Compose config and upstream instrumentation validated.

## Current phase
Phase 12 acceptance implemented; phase 13 documentation and final review in progress.

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
- Acceptance command emits JSON/Markdown/JUnit evidence for all П-1…П-12.
- Shared gateway DNS, explicit transit packet counter probe and bounded night window.
- Run calendar date preserved across midnight; rebuild includes recheck archives.
- Fresh node-side gates evaluated under the deployment lock; expiring recheck evidence.
- Budget module filtering wired to blockcheck; re-enabled modules reset their observation sample.
- Installed CLI verified; 62 tests pass and live topology test skips without enabled lab.
- Real Mistral evaluation is a separate explicit `harness llm-eval --live` command.

## Remaining
- Complete README, requirements mapping, live-verification guide and final verification.
- Real Docker build and networking verification remain environment-dependent.

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
