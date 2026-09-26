import json


def reconcile(root, control):
    expected_path = root / "state" / "expected.json"
    live = control.call("get_config")
    if not expected_path.exists():
        return {"status": "UNKNOWN", "reason": "expected snapshot not initialized", "live": live}
    expected = json.loads(expected_path.read_text())
    return {
        "status": "PASS" if expected["strategy"] == live["strategy"] else "DRIFT",
        "expected": expected,
        "live": live,
    }
