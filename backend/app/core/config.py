"""Configuration settings."""
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "Omni Logistics API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql://omni_user:omni_password@127.0.0.1:15432/omni_logistics"
    auto_create_schema: bool = False
    timescaledb_enabled: bool = True

    # Security
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    refresh_token_entropy_bytes: int = 64
    bootstrap_admin_email: str = "tino@omnilogistics.co.zw"
    bootstrap_admin_password: Optional[str] = None
    vin_decode_timeout_seconds: float = 8.0
    compliance_storage_dir: str = str(PROJECT_ROOT / "storage" / "compliance_evidence")

    # MQTT
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_prefix: str = "vehicles"

    # Email / notifications
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_from: Optional[str] = None
    admin_notify_emails: Optional[str] = None

    # CORS
    allowed_origins: str = ",".join(
        [
            "https://omnilogistics.co.zw",
            "https://www.omnilogistics.co.zw",
            "https://admin.omnilogistics.co.zw",
            "https://client.omnilogistics.co.zw",
            "https://api.omnilogistics.co.zw",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]
    )
    allowed_origin_regex: Optional[str] = (
        r"https?://((localhost|127\.0\.0\.1)(:\d+)?|([a-z0-9-]+\.)?omnilogistics\.co\.zw)$"
    )

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(BACKEND_DIR / ".env"),
        ),
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"development", "staging", "production"}:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        return normalized

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if len(cleaned) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return cleaned

    @property
    def cors_allowed_origins(self) -> List[str]:
        """Return allowed origins as a normalized list for CORS middleware."""
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


settings = Settings()
