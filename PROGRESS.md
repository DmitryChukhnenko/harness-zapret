# Current state

## Last completed phase
Repository inspected; supplied SPEC.md read in full.

## Current phase
Phase 0 — bootstrap.

## Completed
- Read the attached implementation brief and authoritative SPEC.md.
- Confirmed production provider: Mistral, mistral-small-latest,
  https://api.mistral.ai/v1/chat/completions, JSON Schema structured outputs.
- Created local Python environment and installed development dependencies.

## Remaining
- Phases 1–13 from the implementation brief: measurement node, facts, gates,
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
