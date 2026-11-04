"""Validated configuration supporting both Playbook and production environment variables."""

import os
from functools import lru_cache
from typing import Any, Literal
from urllib.parse import urlsplit

from config import (
    BaseSettings,
    Field,
    HttpUrl,
    SecretStr,
    SettingsConfigDict,
    field_validator,
    model_validator,
)


class Settings(BaseSettings):
    """Load environment variables, with real environment taking precedence."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    environment: Literal["production", "development"] = "production"
    enable_simulator: bool = False
    simulator_token: SecretStr = SecretStr("")
    simulator_path: str = "data/simulator/sessions.json"
    local_memory_path: str = "data/local_sessions.json"
    astra_db_api_endpoint: HttpUrl | None = None
    astra_db_application_token: SecretStr = SecretStr("")
    astra_db_keyspace: str = Field(
        default="default_keyspace", pattern=r"^[A-Za-z][A-Za-z0-9_]{0,47}$"
    )
    astra_db_collection: str = Field(
        default="thirdhand_sessions", pattern=r"^[A-Za-z][A-Za-z0-9_]{0,47}$"
    )
    astra_db_collection_name: str = ""
    session_hash_key: SecretStr
    session_ttl_seconds: int = Field(default=86400, ge=60, le=2592000)
    chat_history_messages: int = Field(default=10, ge=2, le=10)
    database_timeout_seconds: float = Field(default=15, gt=0, le=120)
    database_conflict_retries: int = Field(default=6, ge=1, le=12)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    openai_api_key: SecretStr = SecretStr("")
    openai_chat_model: str = "gpt-4o"
    openai_transcription_model: str = "whisper-1"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_chat_model: str = "gemini-2.5-flash"

    meta_access_token: SecretStr = SecretStr("")
    whatsapp_token: SecretStr = SecretStr("")
    meta_phone_number_id: str = ""
    whatsapp_phone_number_id: str = ""
    meta_verify_token: SecretStr = SecretStr("")
    verify_token: SecretStr = SecretStr("")
    meta_app_secret: SecretStr = SecretStr("")
    app_secret: SecretStr = SecretStr("")
    meta_api_version: str = Field(default="", pattern=r"^(?:v[0-9]+\.[0-9]+)?$")

    provider_registry: str = ""
    enable_open_meteo: bool = False

    rapidapi_key: SecretStr = SecretStr("")
    rapidapi_rail_host: str = "irctc1.p.rapidapi.com"
    rapidapi_host: str = ""
    google_places_api_key: SecretStr = SecretStr("")
    google_maps_api_key: SecretStr = SecretStr("")
    google_routes_api_key: SecretStr = SecretStr("")
    amadeus_client_id: SecretStr = SecretStr("")
    amadeus_client_secret: SecretStr = SecretStr("")
    amadeus_environment: Literal["test", "production"] = "test"

    demo_fallback: bool = False
    use_local_memory_fallback: bool = False
    http_timeout_seconds: float = Field(default=30, gt=0, le=120)
    media_max_bytes: int = Field(default=20971520, ge=1024, le=26214400)
    playwright_headless: bool = True
    browser_channel: Literal["chromium", "chrome", "msedge"] = "chromium"
    inbox_path: str = "data/inbox.sqlite3"
    inbox_max_pending: int = Field(default=1000, ge=1)
    job_lease_seconds: int = Field(default=300, ge=10, le=3600)
    processing_timeout_seconds: int = Field(default=240, ge=1, le=600)
    webhook_max_bytes: int = Field(default=1048576, ge=1024)
    booking_profiles_path: str = "config/booking_profiles.json"
    browser_timeout_ms: int = Field(default=30000, ge=1000, le=120000)

    @model_validator(mode="before")
    @classmethod
    def map_playbook_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        if not values.get("meta_access_token") and values.get("whatsapp_token"):
            values["meta_access_token"] = values["whatsapp_token"]
        if not values.get("meta_phone_number_id") and values.get(
            "whatsapp_phone_number_id"
        ):
            values["meta_phone_number_id"] = values["whatsapp_phone_number_id"]
        if not values.get("meta_verify_token") and values.get("verify_token"):
            values["meta_verify_token"] = values["verify_token"]
        if not values.get("meta_app_secret") and values.get("app_secret"):
            values["meta_app_secret"] = values["app_secret"]
        if not values.get("google_places_api_key") and values.get(
            "google_maps_api_key"
        ):
            values["google_places_api_key"] = values["google_maps_api_key"]
        if not values.get("google_routes_api_key") and values.get(
            "google_maps_api_key"
        ):
            values["google_routes_api_key"] = values["google_maps_api_key"]
        if not values.get("rapidapi_rail_host") and values.get("rapidapi_host"):
            values["rapidapi_rail_host"] = values["rapidapi_host"]
        if values.get("astra_db_collection_name") and not values.get(
            "astra_db_collection"
        ):
            values["astra_db_collection"] = values["astra_db_collection_name"]
        return values

    @field_validator("astra_db_api_endpoint")
    @classmethod
    def validate_endpoint(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value is None:
            return None
        parsed = urlsplit(str(value))
        if parsed.scheme != "https" or not (parsed.hostname or "").endswith(
            ".apps.astra.datastax.com"
        ):
            raise ValueError("Use an HTTPS Astra DB Data API endpoint")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Endpoint must not contain credentials, query or fragment")
        if parsed.path not in (None, "", "/"):
            raise ValueError("Use the database origin without an API path")
        return value

    @field_validator("astra_db_application_token")
    @classmethod
    def validate_token(cls, value: SecretStr) -> SecretStr:
        return value

    @field_validator("session_hash_key")
    @classmethod
    def validate_hash_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("SESSION_HASH_KEY must contain at least 32 bytes")
        return value

    @model_validator(mode="after")
    def validate_storage(self) -> "Settings":
        if not self.use_local_memory_fallback:
            if self.astra_db_api_endpoint is None:
                raise ValueError("ASTRA_DB_API_ENDPOINT is required for Astra storage")
            if not self.astra_db_application_token.get_secret_value().strip():
                raise ValueError("An Astra application token is required")
        if self.environment == "production":
            if (
                self.demo_fallback
                or self.use_local_memory_fallback
                or self.enable_simulator
            ):
                raise ValueError(
                    "Demo, local memory and simulator require development mode"
                )
            if self.session_hash_key.get_secret_value().startswith(
                "thirdhand_default_"
            ):
                raise ValueError("Generate a private SESSION_HASH_KEY")
        if (
            self.enable_simulator
            and len(self.simulator_token.get_secret_value().encode()) < 32
        ):
            raise ValueError("SIMULATOR_TOKEN must contain at least 32 bytes")
        if self.processing_timeout_seconds >= self.job_lease_seconds:
            raise ValueError("Job lease must exceed the processing timeout")
        return self

    def validate_startup(self) -> None:
        """No inferred demo mode, default credentials or silent SDK substitutes."""
        self.validate_storage()
        for field in ("meta_access_token", "meta_verify_token", "meta_app_secret"):
            value = getattr(self, field).get_secret_value().strip()
            if (not value and self.environment == "production") or value in {
                "demo-whatsapp-token",
                "thirdhand_verify_2026",
                "demo-app-secret",
                "local-fallback-token",
                "changeme",
                "change-me",
            }:
                raise ValueError(f"Required credential missing or unsafe: {field}")
        if self.environment == "development":
            return
        if (
            not self.meta_phone_number_id.isascii()
            or not self.meta_phone_number_id.isdigit()
        ):
            raise ValueError("META_PHONE_NUMBER_ID must be numeric")
        if not self.meta_api_version:
            raise ValueError(
                "Set META_API_VERSION to an explicitly verified supported version"
            )
        if not (
            self.openai_api_key.get_secret_value().strip()
            or self.gemini_api_key.get_secret_value().strip()
        ):
            raise ValueError(
                "Required credential missing: openai_api_key or gemini_api_key"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load explicit configuration once. Invalid configuration always fails closed."""
    return Settings(_env_file=os.getenv("THIRDHAND_ENV_FILE", ".env"))
