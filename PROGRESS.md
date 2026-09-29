# Current state

## Last completed phase
Phases 0–12 implemented and committed. Docker build and live topology verified on 2026-09-29.

## Current phase
Phase 13: live blockcheck/service checks, final documentation and acceptance evidence.

## Completed
- Three-container Compose lab: harness, Zapret2 gateway, independent routed client.
- Zapret2 pinned at 00f5aaa36de500971faf6db440dd7d8b25672281; instrumented trusted event sidecar.
- Raw archives, typed SQLite facts, idempotent ingestion/rebuild, canonical clean wins and gates.
- Dual-point probes/rechecks, expiring exclusion lease, deterministic invariants and module budget.
- Production MistralProvider uses only MISTRAL_API_KEY, mistral-small-latest and official chat completions JSON Schema output.
- Provider protocol, MockProvider, constrained index selection, schema retry, five typed LLM lanes and evaluations.
- One-line deployment, durable backup, independent local watchdog, rollback, external reconciliation and reports.
- CLI, tests for all acceptance criteria, generated requirements mapping and Russian setup guide.
- 69 offline tests pass on Windows; one opt-in live test skipped there; ruff check passes.
- Docker Desktop engine 29.8.0 started; all three images built and containers started.
- Fixed missing libcap build dependency and Docker internal-bridge transit filtering.
- Live doctor: nftables/nfqws2 available, client route through 172.31.0.2, 27 forwarded packets, OPEN probe.
- Live topology test passed inside the harness container.
- Fixed watchdog repair-domain scope and refreshed reports after rechecks.

## Remaining
- Complete bounded real blockcheck and lifecycle diagnostics; archive results.
- Rebuild final images after fixes; run final unit/acceptance/live checks.
- Update README, requirements/live guide and final checkpoint commit.

## Known issues
- No MISTRAL_API_KEY supplied: actual paid Mistral call has not been made.
- External report sink is not configured; external delivery acceptance remains open.
- No real two-date DPI qualification claimed. Simulated acceptance is labelled separately.

## Verification commands
- `.venv/Scripts/python.exe -m pytest -q`
- `.venv/Scripts/python.exe -m ruff check harness zapret tests tools`
- `docker compose build`
- `docker compose up -d`
- `docker compose exec harness harness doctor`
- `docker compose exec -e HARNESS_LIVE_TESTS=1 harness python -m pytest -m live -q`
- `docker compose exec harness harness acceptance`

## Important architectural decisions
- No privileged containers, Docker socket or arbitrary shell control API.
- Management network is internal. Lab bridge has no host IPv4 gateway or masquerade;
  explicit client route and Zapret NAT provide the sole exit. Uplink gets gateway priority.
- LLM receives only bounded typed summaries and never determines admission or strategy text.
- Local rollback state survives loss of the harness. Live diagnostic data is separate from admission history.
