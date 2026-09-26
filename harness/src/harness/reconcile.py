import json


def reconcile(root, control):
    expected_path = root / "state" / "expected.json"
    live = control.call("get_config")
    if not expected_path.exists():
        return {"status": "UNKNOWN", "reason": "expected snapshot not initialized", "live": live}
    expected = json.loads(expected_path.read_text())
    try:
        client = control.call("client_health")
        routes = client.get("route", [])
        client_ok = len(routes) == 1 and routes[0].get("gateway") == "172.31.0.2"
    except Exception:
        client, client_ok = {"status": "UNMEASURED"}, None
    return {
        "status": "UNKNOWN"
        if client_ok is None
        else "PASS"
        if expected["strategy"] == live["strategy"] and client_ok
        else "DRIFT",
        "expected": expected,
        "live": live,
        "client": client,
    }
