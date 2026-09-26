# Current state

## Last completed phase
Phases 0–1 committed; Compose config and upstream instrumentation validated.

## Current phase
Phases 2–4 — raw run transport, typed facts, SQLite ingestion and gates implemented.

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

## Remaining
- Phases 5–13: client probes, recheck, invariants, LLM, deployment, watchdog,
  reports, acceptance and full operational CLI.

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
