import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration required to connect to PostgreSQL."""

    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class AppConfig:
    """Application configuration for Phoenix ETL."""

    database: DatabaseConfig
    log_level: str


def load_config() -> AppConfig:
    """Load Phoenix ETL configuration from environment variables."""

    return AppConfig(
        database=DatabaseConfig(
            host=os.getenv("PHOENIX_DB_HOST", "localhost"),
            port=int(os.getenv("PHOENIX_DB_PORT", "5432")),
            name=os.getenv("PHOENIX_DB_NAME", "phoenix_etl"),
            user=os.getenv("PHOENIX_DB_USER", "postgres"),
            password=os.getenv("PHOENIX_DB_PASSWORD", ""),
        ),
        log_level=os.getenv("PHOENIX_LOG_LEVEL", "INFO").upper(),
    )
