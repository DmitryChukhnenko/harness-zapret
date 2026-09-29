import os

import pytest
from harness.cli import doctor
from harness.config import load_config
from harness.control import Control


@pytest.mark.live
def test_live_topology_and_firewall():
    if os.environ.get("HARNESS_LIVE_TESTS") != "1":
        pytest.skip("SKIPPED_ENVIRONMENT: set HARNESS_LIVE_TESTS=1 inside the running Docker lab")
    result = doctor(load_config())
    health = Control().call("health")
    assert result["topology"] == "PASS"
    assert health["firewall"] and health["blockcheck"] and health["nfqws"]
