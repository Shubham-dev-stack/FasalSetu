from functools import lru_cache

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
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
