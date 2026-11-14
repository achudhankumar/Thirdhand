"""Public configuration types for the required Pydantic 2 runtime."""

import os

for _env_key in ("NO_PROXY", "no_proxy"):
    _val = os.environ.get(_env_key, "")
    if "[::1]" in _val:
        os.environ[_env_key] = ",".join(
            part for part in _val.split(",") if part.strip() != "[::1]"
        )

from pydantic import (  # noqa: E402
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    JsonValue,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: E402

__all__ = [
    "BaseModel",
    "BaseSettings",
    "ConfigDict",
    "Field",
    "HttpUrl",
    "JsonValue",
    "SecretStr",
    "SettingsConfigDict",
    "ValidationError",
    "field_validator",
    "model_validator",
]
