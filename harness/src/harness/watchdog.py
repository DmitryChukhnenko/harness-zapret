"""Deterministic state machine, run on the gateway independently of Harness/LLM."""

from copy import deepcopy


def make_state(old, new, baselines, now, config):
    repair, guard = [], []
    for key, outcome in baselines.items():
        if outcome["verdict"] == "OPEN":
            guard.append(key)
        elif outcome["verdict"] == "BLOCKED_OR_FAILED":
            repair.append(key)
        else:
            raise ValueError("baseline incomplete; deployment cannot infer unmeasured state")
    return {
        "status": "observing",
        "old": old,
        "new": new,
        "started": now,
        "repair_deadline": now + config.watchdog.repair_wait_seconds,
        "deadline": now + config.watchdog.observation_seconds,
        "repair": repair,
        "guard": guard,
        "repaired": [],
        "failures": {},
        "last_tick": None,
        "unmeasured": [],
    }


def tick(state, observations, now, config):
    result = deepcopy(state)
    if state["status"] != "observing":
        return result, "closed"
    result["last_tick"] = now
    result["unmeasured"] = []
    for key in state["repair"] + state["guard"]:
        outcome = observations.get(key, {"verdict": "UNMEASURED", "success_count": 0})
        if outcome["verdict"] in {"UNMEASURED", "ADDRESS_NOT_SERVING_HOST"}:
            result["unmeasured"].append(key)
            result["failures"][key] = 0
            continue
        failed = outcome["verdict"] == "BLOCKED_OR_FAILED" and outcome["success_count"] == 0
        result["failures"][key] = state["failures"].get(key, 0) + 1 if failed else 0
        if not failed and key in state["repair"] and key not in result["repaired"]:
            result["repaired"].append(key)
        enough = result["failures"][key] >= config.watchdog.consecutive_failures_before_rollback
        if enough and (key in state["guard"] or now >= state["repair_deadline"]):
            result["status"] = "rollback_required"
            return result, "guard_failed" if key in state["guard"] else "repair_failed"
    if now >= state["deadline"]:
        unresolved = set(state["repair"]) - set(result["repaired"])
        result["status"] = "closed_inconclusive" if unresolved else "accepted"
        return result, result["status"]
    return result, "observing"
