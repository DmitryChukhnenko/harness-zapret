import pytest
from harness.config import Config, Domains, load_config, load_domains
from pydantic import ValidationError


def test_repository_configuration():
    assert load_config().llm.model == "mistral-small-latest"
    assert load_config().llm.provider == "mistral"
    assert load_domains().all() == ["example.com", "example.org"]


def test_secrets_and_unsafe_domain_are_rejected():
    with pytest.raises(ValidationError):
        Config.model_validate({"llm": {"api_key": "not-allowed"}})
    with pytest.raises(ValidationError):
        Domains(classes={"bad": ["example.org; id"]})


def test_cli_config_error_does_not_echo_secret(tmp_path, monkeypatch, capsys):
    from harness.cli import main

    path = tmp_path / "invalid.yaml"
    path.write_text("llm:\n  api_key: secret-sentinel-must-not-print\n")
    monkeypatch.setattr("sys.argv", ["harness", "doctor", "--config", str(path)])
    assert main() == 1
    assert "secret-sentinel" not in capsys.readouterr().out
