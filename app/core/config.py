from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tinnova Vehicle API"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    secret_key: str = "tinnova-vehicle-api-super-secret-key-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "tinnova_vehicle_db"
    postgres_user: str = "tinnova"
    postgres_password: str = "tinnova"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_ttl_usd_brl: int = 300

    exchange_rate_primary_url: str = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    exchange_rate_fallback_url: str = "https://api.frankfurter.app/latest?from=USD&to=BRL"
    exchange_rate_timeout_seconds: int = 5

    seed_admin_username: str = "admin"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "Admin123!"

    seed_user_username: str = "user"
    seed_user_email: str = "user@example.com"
    seed_user_password: str = "User123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY deve ter no mínimo 32 caracteres.")
        return value

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
