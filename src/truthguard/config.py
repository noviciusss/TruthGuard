"""Configuration loading with environment overrides and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _load_local_env() -> None:
    """Load a simple project ``.env`` without adding a runtime dependency.

    This intentionally supports only the KEY=value format used by
    ``.env.example``. Existing process environment variables always win, and
    values are stripped of Windows line endings so a Windows-created file also
    works inside Linux/Docker.
    """

    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and apply the small set of environment overrides."""

    _load_local_env()
    config_path = Path(path or os.getenv("TRUTHGUARD_CONFIG", ROOT / "config.yaml"))
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    project = config.setdefault("project", {})
    project["offline"] = _as_bool(os.getenv("TRUTHGUARD_OFFLINE", project.get("offline", True)))
    project["data_dir"] = os.getenv("TRUTHGUARD_DATA_DIR", project.get("data_dir", "data"))
    project["cache_dir"] = os.getenv("TRUTHGUARD_CACHE_DIR", project.get("cache_dir", "data/cache"))
    return config


def provider_is_configured(provider: str, config: dict[str, Any] | None = None) -> bool:
    """Return whether a provider has a non-empty API key in the environment."""

    config = config or load_config()
    provider_config = config.get("providers", {}).get(provider, {})
    variable = provider_config.get("api_key_env")
    return bool(variable and os.getenv(variable))


if __name__ == "__main__":
    loaded = load_config()
    print(f"{loaded['project']['name']} configuration loaded (offline={loaded['project']['offline']})")
