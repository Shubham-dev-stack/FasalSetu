from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DEMO_MODE: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-only-placeholder-32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    DATABASE_URL: str = "sqlite:///./data/app.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    APP_TIMEZONE: str = "Asia/Kolkata"
    ROUTING_PROVIDER: str = "haversine"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    OSRM_TIMEOUT_S: int = 5
    ROAD_CIRCUITY_FACTOR: float = 1.35
    SOLVER_TIME_LIMIT_S: int = 5
    MODEL_DIR: str = "ml/artifacts"
    PRICE_SOURCE: str = "synthetic"
    AGMARKNET_SNAPSHOT_PATH: str = "data/raw/agmarknet_snapshot.csv"
    DATA_GOV_IN_API_KEY: str = ""
    ALLOW_DEMO_RESET: bool = True
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.APP_ENV == "production":
            if "change-in-production" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                if self.DEMO_MODE:
                    import secrets

                    # Generate an ephemeral cryptographically secure 64-char key at boot
                    # so default placeholder is never active in production demo containers
                    self.SECRET_KEY = secrets.token_urlsafe(32)
                else:
                    raise ValueError(
                        "SECRET_KEY must be a cryptographically secure string (minimum 32 characters) in production."
                    )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
