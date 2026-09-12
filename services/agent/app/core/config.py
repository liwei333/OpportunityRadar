"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./data/opportunity_radar.db"

    # Browser
    browser_headless: bool = True
    browser_user_data_dir: str = "./data/browser_profile"

    # LLM
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    @property
    def database_path(self) -> Path:
        """Extract filesystem path from SQLite URL."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return Path(url.replace("sqlite:///", "", 1))
        if url.startswith("sqlite://"):
            return Path(url.replace("sqlite://", "", 1))
        return Path("data/opportunity_radar.db")

    @property
    def async_database_url(self) -> str:
        """Return async-compatible SQLAlchemy URL."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    # Ensure parent directory for database exists
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
