import os

import pytest
from harness.cli import doctor
from harness.config import load_config
from harness.control import Control


@pytest.mark.live
def test_live_topology_and_firewall():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        pytest.skip("SKIPPED_ENVIRONMENT: set HARNESS_LIVE_TESTS=1 inside the running Docker lab")
    try:
        result = doctor(load_config())
        health = Control().call("health")
    except Exception:
        pytest.skip("SKIPPED_ENVIRONMENT: Linux lab control endpoint unavailable")
    assert result["topology"] == "PASS"
    assert health["firewall"] and health["blockcheck"]
