from datetime import UTC, datetime

import pytest
from harness.models import Fact


@pytest.fixture
def fact():
    def make(**changes):
        fields = dict(
            run_id="run-1",
            timestamp=datetime(2026, 9, 25, tzinfo=UTC),
            sequence=0,
            record_type="probe",
            domain="example.org",
            address_family=4,
            protocol="https_tls12",
            source="fixture",
            strategy="--payload=tls_client_hello",
            verdict="OPEN",
            success_count=2,
            attempt_count=2,
            frontend_addresses=["192.0.2.1", "192.0.2.2"],
            measurement_point="gateway",
        )
        return Fact(**(fields | changes))

    return make
