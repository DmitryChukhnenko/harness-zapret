from datetime import datetime
from ipaddress import ip_address
from typing import Literal

from pydantic import Field, computed_field, model_validator

from harness.config import StrictModel

Point = Literal["gateway", "client"]
Verdict = Literal["OPEN", "BLOCKED_OR_FAILED", "ADDRESS_NOT_SERVING_HOST", "UNMEASURED"]


class Fact(StrictModel):
    run_id: str
    timestamp: datetime
    sequence: int = Field(ge=0)
    record_type: Literal["probe", "baseline", "foreign"]
    domain: str
    address_family: Literal[4, 6]
    protocol: str
    source: str
    strategy: str
    verdict: Verdict
    success_count: int = Field(ge=0)
    attempt_count: int = Field(ge=1)
    frontend_addresses: list[str]
    measurement_point: Point

    @computed_field
    @property
    def frontend_address_count(self) -> int:
        return len(set(self.frontend_addresses))

    @model_validator(mode="after")
    def consistent(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must include timezone")
        if self.success_count > self.attempt_count:
            raise ValueError("successes exceed attempts")
        for address in self.frontend_addresses:
            if ip_address(address).version != self.address_family:
                raise ValueError("frontend address family mismatch")
        if len(set(self.frontend_addresses)) > self.attempt_count:
            raise ValueError("more addresses than attempts")
        return self


class Invariant(StrictModel):
    name: str
    status: Literal["PASS", "FAIL", "UNKNOWN"]
    reason: str
    evidence: dict[str, int | bool | str] = Field(default_factory=dict)


class GateResult(StrictModel):
    class_name: str
    strategy: str
    protocol: str
    address_family: Literal[4, 6]
    eligible: bool
    reasons: list[str]
    clean_wins: int
    runs: int
    dates: int
    domains: list[str]
