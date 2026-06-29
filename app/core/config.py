"""Configuration FrontierPay V23"""
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    APP_NAME: str = "FrontierPay"
    VERSION: str = "23.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://fp:fp@localhost/frontierpay_v23", env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")

    # Security
    SECRET_KEY: SecretStr = Field(default=SecretStr("change-me-in-production"), env="SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # KoraPay
    KORA_PUBLIC_KEY: SecretStr = Field(default=SecretStr(""), env="KORA_PUBLIC_KEY")
    KORA_SECRET_KEY: SecretStr = Field(default=SecretStr(""), env="KORA_SECRET_KEY")
    KORA_BASE_URL: str = Field(default="https://api.korapay.com", env="KORA_BASE_URL")

    # Fincra
    FINCRA_API_KEY: SecretStr = Field(default=SecretStr(""), env="FINCRA_API_KEY")
    FINCRA_SECRET_KEY: SecretStr = Field(default=SecretStr(""), env="FINCRA_SECRET_KEY")
    FINCRA_BASE_URL: str = Field(default="https://api.fincra.com", env="FINCRA_BASE_URL")

    # Payoneer
    PAYONEER_CLIENT_ID: SecretStr = Field(default=SecretStr(""), env="PAYONEER_CLIENT_ID")
    PAYONEER_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""), env="PAYONEER_CLIENT_SECRET")

    # AI Support
    AI_MODEL: str = Field(default="gpt-4", env="AI_MODEL")
    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")

    # Telemetry
    JAEGER_ENDPOINT: str = Field(default="http://localhost:14268/api/traces", env="JAEGER_ENDPOINT")

    # Kaybic
    KAYBIC_WEBHOOK_SECRET: SecretStr = Field(default=SecretStr(""), env="KAYBIC_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
