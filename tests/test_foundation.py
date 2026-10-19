from __future__ import annotations

from pathlib import Path

from truthguard.config import load_config, provider_is_configured


def test_config_contains_required_sections() -> None:
    config = load_config()
    assert config["project"]["name"] == "TruthGuard"
    assert config["project"]["domain"] == "Aurelia Health"
    assert config["retrieval"]["final_k"] == 8
    assert config["role_chains"]["synthesizer"][0] == "groq"


def test_config_path_is_inside_project() -> None:
    config = load_config()
    data_dir = Path(config["project"]["data_dir"])
    assert not data_dir.is_absolute()


def test_provider_is_not_configured_without_key(monkeypatch) -> None:
    monkeypatch.delenv("TEST_MISSING_PROVIDER_KEY", raising=False)
    config = {"providers": {"groq": {"api_key_env": "TEST_MISSING_PROVIDER_KEY"}}}
    assert provider_is_configured("groq", config) is False


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("TRUTHGUARD_OFFLINE", "false")
    monkeypatch.setenv("TRUTHGUARD_DATA_DIR", "tmp-data")
    config = load_config()
    assert config["project"]["offline"] is False
    assert config["project"]["data_dir"] == "tmp-data"
