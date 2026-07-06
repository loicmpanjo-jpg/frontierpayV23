"""Production-hardened configuration with Pydantic v2 validation."""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = Field(..., min_length=48)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        if len(v) < 48:
            raise ValueError(f"SECRET_KEY must be >=48 characters, got {len(v)}")
        return v

    database_url: str = Field(..., pattern=r"^postgresql\+asyncpg://")
    db_pool_size: int = Field(default=20, ge=5, le=100)
    db_max_overflow: int = Field(default=30, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5, le=120)

    redis_url: str = Field(..., pattern=r"^redis://")
    redis_pool_size: int = Field(default=50, ge=10, le=200)

    kora_api_key: str | None = None
    kora_secret_key: str | None = None
    fincra_api_key: str | None = None
    fincra_secret_key: str | None = None
    flutterwave_public_key: str | None = None
    flutterwave_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_secret_key: str | None = None

    kora_webhook_secret: str | None = None
    fincra_webhook_secret: str | None = None

    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_logs: bool = True

    allowed_origins: str = "http://localhost:3000"

    ads_share: float = Field(default=0.35, ge=0.0, le=1.0)
    creator_share: float = Field(default=0.50, ge=0.0, le=1.0)
    platform_share: float = Field(default=0.15, ge=0.0, le=1.0)

    enable_copy_trading: bool = True
    enable_social_trading: bool = True
    max_copy_allocation_percent: int = Field(default=100, ge=1, le=100)

    def get_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
