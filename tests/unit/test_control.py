import pytest
from harness.node import dispatch
from pydantic import ValidationError


def test_control_has_no_execution_verb():
    with pytest.raises(ValueError, match="unsupported"):
        dispatch("gateway", "exec", {"command": "arbitrary"})


def test_invalid_apply_arguments_rejected_before_engine(monkeypatch):
    monkeypatch.setattr("harness.node_runtime.engine", lambda: pytest.fail("state touched"))
    with pytest.raises(ValidationError):
        dispatch("gateway", "apply_strategy", {"run_id": "invalid", "strategy": "--payload=x"})
