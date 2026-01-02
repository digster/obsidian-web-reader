"""Application configuration using Pydantic Settings."""

import secrets
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App settings
    app_name: str = "Obsidian Web Reader"
    env: Literal["development", "production"] = "production"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Authentication
    app_password: str = Field(..., description="Password for accessing the app")
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Secret key for JWT signing",
    )
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Vault configuration
    vaults_config: Path = Field(
        default=Path("./vaults.json"),
        description="Path to vault configuration file",
    )
    vaults_dir: Path = Field(
        default=Path("./vaults"),
        description="Directory where cloned vault repositories are stored",
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for storing search indexes and app data",
    )

    # CORS settings (for development)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            # Handle comma-separated string from env var
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("vaults_config", "data_dir", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"


# Global settings instance
settings = Settings()

