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
