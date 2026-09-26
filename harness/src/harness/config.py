"""Validated local configuration; secrets are deliberately not configuration fields."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Measurement(StrictModel):
    min_distinct_addresses: int = Field(default=2, ge=2)
    attempts_per_domain: int = Field(default=2, ge=2, le=20)


class Gates(StrictModel):
    min_runs: int = Field(default=2, ge=2)
    min_dates: int = Field(default=2, ge=2)


class Watchdog(StrictModel):
    consecutive_failures_before_rollback: int = Field(default=2, ge=2)
    repair_wait_seconds: int = Field(default=600, ge=1)
    observation_seconds: int = Field(default=7200, ge=1)
    tick_seconds: int = Field(default=30, ge=1)

    @model_validator(mode="after")
    def window(self):
        if self.observation_seconds < self.repair_wait_seconds:
            raise ValueError("observation window must include the repair wait")
        return self


class Budget(StrictModel):
    zero_win_elimination_threshold: int = Field(default=1000, ge=1)
    module_reenable_days: int = Field(default=14, ge=1)


class Timeouts(StrictModel):
    control_seconds: int = Field(default=2, ge=1, le=60)
    exit_probe_seconds: int = Field(default=5, ge=1, le=60)


class LLMConfig(StrictModel):
    provider: Literal["mistral", "mock"] = "mistral"
    model: str = "mistral-small-latest"
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    max_tokens: int = Field(default=1024, ge=64, le=8192)
    max_summary_bytes: int = Field(default=16384, ge=1024, le=65536)


class Config(StrictModel):
    measurement: Measurement = Field(default_factory=Measurement)
    gates: Gates = Field(default_factory=Gates)
    watchdog: Watchdog = Field(default_factory=Watchdog)
    budget: Budget = Field(default_factory=Budget)
    timeouts: Timeouts = Field(default_factory=Timeouts)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    data_dir: str = "data"


class Domains(StrictModel):
    classes: dict[str, list[str]]

    @field_validator("classes")
    @classmethod
    def valid_domains(cls, value):
        import re

        if not value or any(not domains for domains in value.values()):
            raise ValueError("classes and domain lists must be nonempty")
        for domains in value.values():
            for domain in domains:
                if not re.fullmatch(r"(?=.{1,253}$)[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?", domain):
                    raise ValueError("invalid domain name")
        return value

    def all(self):
        return sorted({domain for domains in self.classes.values() for domain in domains})


def load_config(path: str | Path = "config/harness.yaml") -> Config:
    return Config.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def load_domains(path: str | Path = "config/domains.yaml") -> Domains:
    return Domains.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
