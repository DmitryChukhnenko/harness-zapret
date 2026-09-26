"""Finite control interface. No command/shell endpoint exists."""

from pathlib import Path

import httpx

ALLOWED = {
    "path_probe",
    "client_health",
    "health",
    "probe",
    "run_blockcheck",
    "run_status",
    "run_result",
    "recheck",
    "get_config",
    "apply_strategy",
    "restore_backup",
    "service_status",
    "watchdog",
}


class Control:
    def __init__(self, endpoint="http://172.30.0.2:8080", timeout=2, token_path="/auth/token"):
        self.endpoint, self.timeout, self.token_path = endpoint, timeout, token_path

    def call(self, verb, arguments=None):
        if verb not in ALLOWED:
            raise ValueError("unsupported control operation")
        token = Path(self.token_path).read_text().strip()
        with httpx.Client(timeout=self.timeout, trust_env=False) as client:
            response = client.post(
                f"{self.endpoint}/{verb}",
                json=arguments or {},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()
