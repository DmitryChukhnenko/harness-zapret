# Current state

## Last completed phase
Phase 0 — bootstrap committed; configuration tests passed (2/2).

## Current phase
Phase 1 — pinned Zapret2 container and finite control interface implemented.

## Completed
- Read the attached implementation brief and authoritative SPEC.md.
- Confirmed production provider: Mistral, mistral-small-latest,
  https://api.mistral.ai/v1/chat/completions, JSON Schema structured outputs.
- Created local Python environment and installed development dependencies.
- Compose validates; instrumenter anchors verified against pinned upstream source.
- Isolated management/lab networks, explicit client default route and gateway NAT.
- Authenticated finite control API, node health checks, CLI doctor.

## Remaining
- Phases 2–13 from the implementation brief: raw runs, facts, gates,
  client, recheck, invariants, LLM, deployment, watchdog, reports, acceptance.

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
