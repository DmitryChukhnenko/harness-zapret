"""One-line transaction with durable pre-mutation backup and recoverable state."""

import json
import time
from pathlib import Path

from harness.locking import lock
from harness.storage import write_json, write_text
from harness.strategy import validate_strategy
from harness.watchdog import make_state, tick


class Deployment:
    def __init__(self, root, config, restart, service, measure, scheduled):
        self.root, self.config = Path(root), config
        self.restart, self.service, self.measure, self.scheduled = (
            restart,
            service,
            measure,
            scheduled,
        )
        self.root.mkdir(parents=True, exist_ok=True)

    def read(self):
        path = self.root / "strategy.conf"
        return path.read_text().rstrip("\n") if path.exists() else ""

    def state(self):
        path = self.root / "deployment.json"
        return json.loads(path.read_text()) if path.exists() else {"status": "idle"}

    def write_strategy(self, strategy):
        write_text(self.root / "strategy.conf", strategy + "\n")

    def apply(self, strategy, *, eligible, now=None, repair_domains=None):
        validate_strategy(strategy)  # Validate before locks and state mutations.
        if not callable(eligible) and not eligible:
            raise ValueError("candidate did not pass deterministic gates")
        with lock(self.root / "operation.lock"):
            if callable(eligible) and not eligible():
                raise ValueError("candidate did not pass fresh deterministic gates")
            if not self.scheduled():
                raise ValueError("local watchdog is not scheduled")
            if strategy == self.read():
                raise ValueError("strategy already installed")
            if self.state()["status"] in {"observing", "prepared", "rollback_required"}:
                raise ValueError("previous deployment still active")
            baselines = self.measure()  # Includes all configured branches and both points.
            old = self.read()
            state = make_state(
                old,
                strategy,
                baselines,
                time.time() if now is None else now,
                self.config,
                repair_domains,
            )
            write_text(self.root / "backup.conf", old + "\n")
            state["status"] = "prepared"
            write_json(self.root / "deployment.json", state)
            self.write_strategy(strategy)
            try:
                self.restart(strategy)
                if not self.service():
                    raise RuntimeError("service failed post-deploy validation")
            except Exception:
                return self._rollback(state, "service_start_failed")
            state["status"] = "observing"
            write_json(self.root / "deployment.json", state)
            return state

    def _rollback(self, state, reason):
        old = (self.root / "backup.conf").read_text().rstrip("\n")
        self.write_strategy(old)
        try:
            self.restart(old)
            restored = self.service()
        except Exception:
            restored = False
        state |= {
            "status": "rolled_back" if restored else "rollback_failed",
            "rollback_reason": reason,
            "rollback_time": time.time(),
        }
        write_json(self.root / "deployment.json", state)
        return state

    def rollback(self, reason="manual"):
        with lock(self.root / "operation.lock"):
            return self._rollback(self.state(), reason)

    def watchdog(self, now=None):
        with lock(self.root / "watchdog.lock"), lock(self.root / "operation.lock"):
            state = self.state()
            if state["status"] == "prepared":
                return self._rollback(state, "interrupted_deployment")
            if state["status"] != "observing":
                return state
            if not self.service():
                return self._rollback(state, "service_died")
            state, reason = tick(
                state, self.measure(), time.time() if now is None else now, self.config
            )
            if state["status"] == "rollback_required":
                return self._rollback(state, reason)
            write_json(self.root / "deployment.json", state)
            return state
