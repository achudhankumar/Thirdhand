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

    astra_db_api_endpoint: HttpUrl
    astra_db_application_token: SecretStr
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
    meta_api_version: str = Field(default="v20.0", pattern=r"^v[0-9]+\.[0-9]+$")

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
        if not values.get("meta_phone_number_id") and values.get("whatsapp_phone_number_id"):
            values["meta_phone_number_id"] = values["whatsapp_phone_number_id"]
        if not values.get("meta_verify_token") and values.get("verify_token"):
            values["meta_verify_token"] = values["verify_token"]
        if not values.get("meta_app_secret") and values.get("app_secret"):
            values["meta_app_secret"] = values["app_secret"]
        if not values.get("google_places_api_key") and values.get("google_maps_api_key"):
            values["google_places_api_key"] = values["google_maps_api_key"]
        if not values.get("google_routes_api_key") and values.get("google_maps_api_key"):
            values["google_routes_api_key"] = values["google_maps_api_key"]
        if not values.get("rapidapi_rail_host") and values.get("rapidapi_host"):
            values["rapidapi_rail_host"] = values["rapidapi_host"]
        if values.get("astra_db_collection_name") and not values.get("astra_db_collection"):
            values["astra_db_collection"] = values["astra_db_collection_name"]
        return values

    @field_validator("astra_db_api_endpoint")
    @classmethod
    def validate_endpoint(cls, value: HttpUrl) -> HttpUrl:
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
        if not value.get_secret_value().strip():
            raise ValueError("An Astra application token is required")
        return value

    @field_validator("session_hash_key")
    @classmethod
    def validate_hash_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("SESSION_HASH_KEY must contain at least 32 bytes")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Validate settings once on application startup, or build safe local defaults when running in demo mode."""
    try:
        return Settings()
    except Exception:
        if os.getenv("THIRDHAND_STRICT_STARTUP", "").lower() in {"1", "true", "yes"}:
            raise
        return Settings(
            _env_file=".env" if os.path.exists(".env") else None,
            astra_db_api_endpoint=os.getenv(
                "ASTRA_DB_API_ENDPOINT",
                "https://local-fallback.apps.astra.datastax.com",
            ),
            astra_db_application_token=os.getenv(
                "ASTRA_DB_APPLICATION_TOKEN", "local-fallback-token"
            ),
            session_hash_key=os.getenv(
                "SESSION_HASH_KEY",
                "thirdhand_default_session_secret_key_change_in_prod_2026",
            ),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            meta_access_token=os.getenv(
                "META_ACCESS_TOKEN", os.getenv("WHATSAPP_TOKEN", "demo-whatsapp-token")
            ),
            meta_phone_number_id=os.getenv(
                "META_PHONE_NUMBER_ID",
                os.getenv("WHATSAPP_PHONE_NUMBER_ID", "100000000000001"),
            ),
            meta_verify_token=os.getenv(
                "META_VERIFY_TOKEN",
                os.getenv("VERIFY_TOKEN", "thirdhand_verify_2026"),
            ),
            meta_app_secret=os.getenv(
                "META_APP_SECRET", os.getenv("APP_SECRET", "demo-app-secret")
            ),
            demo_fallback=True,
            use_local_memory_fallback=not bool(
                os.getenv("ASTRA_DB_API_ENDPOINT", "").strip()
            ),
        )
