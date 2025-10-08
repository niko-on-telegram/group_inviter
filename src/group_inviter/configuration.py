"""Configuration loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SettingsBase(BaseModel):
    """Base settings model."""

    model_config = ConfigDict(protected_namespaces=())


class TelegramConfig(SettingsBase):
    """Telegram-specific settings."""

    bot_token: str = Field(..., min_length=10)
    parse_mode: str = Field("HTML", min_length=1)
    admin_chat_id: int | None = Field(default=None, ge=1)


class LoggingConfig(SettingsBase):
    """Logging parameters."""

    level: str = Field("INFO", min_length=1)
    structured: bool = Field(False, alias="json")
    directory: Path = Field(Path("logs"))
    info_filename: str = Field("info.log", min_length=1)
    debug_filename: str = Field("debug.log", min_length=1)
    timezone: str = Field("UTC", min_length=1)


class MetricsConfig(SettingsBase):
    """Metrics exposition settings."""

    enabled: bool = Field(True)
    host: str = Field("127.0.0.1", min_length=1)
    port: int = Field(8000, ge=1, le=65535)


class AppConfig(SettingsBase):
    """Aggregate application configuration."""

    telegram: TelegramConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)


DEFAULT_CONFIG_PATH = Path("config/config.yaml")
CONFIG_ENV_VAR = "GROUP_INVITER_CONFIG"


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except FileNotFoundError as exc:  # pragma: no cover - interactive usage
        msg = f"Configuration file not found: {path}"
        raise FileNotFoundError(msg) from exc
    if not isinstance(data, dict):
        msg = "Configuration root should be a mapping"
        raise ValueError(msg)
    return data


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from YAML or raise a descriptive error."""

    config_path = path or Path(os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH))
    raw_data = _read_yaml(config_path)
    try:
        return AppConfig.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc
