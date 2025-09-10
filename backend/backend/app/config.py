from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeviceJwtKeys(BaseModel):
    active_kid: str
    keys: dict[str, str]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    environment: str = Field(default="dev")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    clickhouse_url: str | None = Field(default=None, alias="CLICKHOUSE_URL")

    access_token_secret: str = Field(alias="ACCESS_TOKEN_SECRET")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_secret: str = Field(alias="REFRESH_TOKEN_SECRET")
    refresh_token_expire_days: int = Field(
        default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    device_jwt_keys_raw: str = Field(alias="DEVICE_JWT_KEYS")
    wss_url: str = Field(alias="WSS_URL")
    node_id: str = Field(default="node-1", alias="NODE_ID")
    kafka_brokers: str | None = Field(default=None, alias="KAFKA_BROKERS")
    minio_endpoint: str | None = Field(default=None, alias="MINIO_ENDPOINT")
    minio_external_endpoint: str | None = Field(
        default=None, alias="MINIO_EXTERNAL_ENDPOINT")
    minio_access_key: str | None = Field(
        default=None, alias="MINIO_ACCESS_KEY")
    minio_secret_key: str | None = Field(
        default=None, alias="MINIO_SECRET_KEY")
    artifacts_bucket: str | None = Field(
        default=None, alias="ARTIFACTS_BUCKET")

    rate_limit_login_per_minute: int = Field(
        default=100, alias="RATE_LIMIT_LOGIN_PER_MINUTE")
    account_lock_threshold: int = Field(
        default=5, alias="ACCOUNT_LOCK_THRESHOLD")
    account_lock_minutes: int = Field(default=15, alias="ACCOUNT_LOCK_MINUTES")
    disable_rate_limiting: bool = Field(
        default=True, alias="DISABLE_RATE_LIMITING")

    # Feature flags / operational toggles
    enable_debug_routes: bool = Field(
        default=True, alias="ENABLE_DEBUG_ROUTES"
    )

    # CORS / Metrics
    allowed_origins_raw: str = Field(default="*", alias="ALLOWED_ORIGINS")
    metrics_token: str | None = Field(default=None, alias="METRICS_TOKEN")

    @property
    def allowed_origins(self) -> list[str]:
        raw = (self.allowed_origins_raw or "").strip()
        if raw in ("", "*"):
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def device_jwt_keys(self) -> DeviceJwtKeys:
        data: dict[str, Any] = json.loads(self.device_jwt_keys_raw)
        return DeviceJwtKeys(**data)


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
