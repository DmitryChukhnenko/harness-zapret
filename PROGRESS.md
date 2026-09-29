# Current state

## Last completed phase
Phases 0–13 completed. Implementation, final images, documented live lab validation and acceptance completed on 2026-09-29.

## Current phase
Ready for installation-specific domain measurements and optional real Mistral evaluation.

## Completed
- Three-container Compose lab: harness, Zapret2 gateway, independent routed client.
- Zapret2 pinned at 00f5aaa36de500971faf6db440dd7d8b25672281; trusted instrumented event sidecar.
- Raw archives, typed SQLite facts, idempotent ingestion/rebuild, canonical clean wins and gates.
- Dual-point probes/rechecks, expiring exclusion lease, deterministic invariants and module budget.
- MistralProvider: only MISTRAL_API_KEY, default mistral-small-latest, official /v1/chat/completions with JSON Schema structured outputs.
- Provider protocol, MockProvider, constrained index selection, one schema retry, five typed LLM lanes and evaluations.
- One-line deployment, durable backup, local watchdog, rollback, external reconciliation and reports.
- 69 offline tests pass on Windows and Linux; 1 opt-in live topology test passes in Docker.
- Offline acceptance: all П-1…П-12 PASS_SIMULATED, 69/69 tests; final Linux report 20260929T071253Z.
- Docker engine 29.8.0: three images built, all containers running.
- Fixed libcap-dev, hexdump and CAP_KILL requirements discovered by actual build/run.
- Fixed internal-bridge transit filtering: lab bridge has no host IPv4 gateway/NAT.
- Live doctor: nftables/nfqws2 available, client route via 172.31.0.2, FORWARD increases, HTTPS OPEN.
- Actual blockcheck smoke: exit 0, 3 facts, 2 strategies, special-character argv roundtrip preserved.
- Actual recheck: 4 OPEN facts, 2 points × 2 domains, at least 2 IPs each; lease cleanup preserves active PID.
- Actual lifecycle: overlap rejection/release, client UNMEASURED without rollback, single bad tick tolerance, guard/repair rollback, observation closure, immediate start-failure rollback and deployment refusals.
- Lifecycle also passed with Harness stopped. With gateway stopped, client cannot bypass it (forced-IP curl timeout).
- External reconciliation detects strategy and client route drift; restored state PASS, empty strategy and idle deployment.
- Compact live evidence with hashes committed under docs/evidence; full local archives under data/reports/live.
- Fixed repair-domain scope, post-recheck report freshness and required standard module includes.
- Russian README, live verification guide, complete mapping of 95 requirements and 12 acceptance cases.

## Remaining
- Installation-specific follow-up: configure real domains and collect full sweeps on two real dates.
- Supply MISTRAL_API_KEY through environment for paid API evaluation; configure optional external ReportSink.

## Known issues / honest limits
- No API key supplied: no paid Mistral call. Official HTTP/structured-output contract tested offline.
- External sink not configured; external-delivery live criterion remains open.
- Live diagnostics use example domains, separate archives, fixture admission and shortened windows.
  They do not prove full-night module allocation, two-date qualification or efficacy against a particular DPI.
- Provider response gives tokens, not billed currency; report cost is null with explicit status.
- Embedded physical-router/tunnel/offload requirements are outside the authorized Docker architecture.

## Verification commands
- `.venv/Scripts/python.exe -m pytest -q`
- `.venv/Scripts/python.exe -m ruff check harness zapret tests tools`
- `docker compose build`
- `docker compose up -d`
- `docker compose exec harness harness doctor`
- `docker compose exec -e HARNESS_LIVE_TESTS=1 harness python -m pytest -m live -q`
- `docker compose exec harness harness acceptance`
- Bounded fault-injection commands and prerequisites: docs/LIVE-VERIFICATION.md.

## Important architectural decisions
- No privileged containers, Docker socket or arbitrary shell control API.
- Internal management network; lab bridge inhibit_ipv4=true and host masquerade=false;
  explicit client route and Zapret NAT provide the sole exit. Uplink has gateway priority.
- LLM receives bounded typed summaries and never determines admission or executable strategy text.
- Local rollback state survives loss of Harness. Diagnostic facts never enter admission history.
- Offline acceptance and live measurements carry separate statuses and evidence.
