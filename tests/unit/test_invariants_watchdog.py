import pytest
from harness.config import Config
from harness.invariants import evaluate_invariants
from harness.locking import BusyError, lock
from harness.watchdog import make_state, tick


def status(verdict, count=0):
    return {"verdict": verdict, "success_count": count}


def test_harm_and_unknown(fact):
    for harmed, expected in [(False, "PASS"), (True, "FAIL"), (None, "UNKNOWN")]:
        result = evaluate_invariants([fact()], overlap_harmed=harmed)
        assert next(i for i in result if i.name == "routing_overlap_harm").status == expected


def test_watchdog_all_branches():
    config = Config()
    baseline = {
        "gateway:example.org": status("BLOCKED_OR_FAILED"),
        "client:example.com": status("OPEN", 2),
    }
    state = make_state("old", "new", baseline, 0, config)
    state, action = tick(state, baseline, 1, config)
    assert action == "observing"
    failed = {key: status("BLOCKED_OR_FAILED") for key in baseline}
    state, action = tick(state, failed, 2, config)
    assert action == "observing"  # single failed guard pass
    rolled, action = tick(state, failed, 3, config)
    assert action == "guard_failed" and rolled["status"] == "rollback_required"
    unknown = {key: status("UNMEASURED") for key in baseline}
    assert tick(state, unknown, 4, config)[1] == "observing"
    restored = {key: status("OPEN", 2) for key in baseline}
    state, _ = tick(state, restored, 5, config)
    assert tick(state, restored, state["deadline"], config)[1] == "accepted"
    repair_only = make_state("old", "new", {"gateway:x": status("BLOCKED_OR_FAILED")}, 0, config)
    repair_only, _ = tick(repair_only, {"gateway:x": status("BLOCKED_OR_FAILED")}, 1, config)
    assert (
        tick(repair_only, {"gateway:x": status("BLOCKED_OR_FAILED")}, 600, config)[1]
        == "repair_failed"
    )


def test_overlap_rejected_then_released(tmp_path):
    path = tmp_path / "watchdog.lock"
    with lock(path):
        with pytest.raises(BusyError):
            with lock(path):
                pytest.fail("overlapping tick entered")
    with lock(path):
        pass


def test_repair_scope_preserves_all_other_guards():
    baseline = {
        "gateway:target.example": status("BLOCKED_OR_FAILED"),
        "client:target.example": status("BLOCKED_OR_FAILED"),
        "gateway:unrelated-broken.example": status("BLOCKED_OR_FAILED"),
        "client:unrelated-open.example": status("OPEN", 2),
        "gateway:transient.example": status("BLOCKED_OR_FAILED", 1),
    }
    state = make_state("old", "new", baseline, 0, Config(), ["target.example"])
    assert state["repair"] == ["gateway:target.example", "client:target.example"]
    assert state["guard"] == ["client:unrelated-open.example", "gateway:transient.example"]


def test_empty_baseline_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        make_state("old", "new", {}, 0, Config())
