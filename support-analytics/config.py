import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"


@dataclass
class Settings:
    """Application level configuration and feature flags."""

    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(DATA_DIR / 'support_analytics.db').as_posix()}",
    )
    ticket_raw_path: Path = Path(
        os.getenv(
            "TICKET_RAW_PATH",
            (DATA_DIR / "raw_tickets.csv").as_posix(),
        )
    )
    telemetry_raw_path: Path = Path(
        os.getenv(
            "TELEMETRY_RAW_PATH",
            (DATA_DIR / "raw_telemetry.csv").as_posix(),
        )
    )
    processed_dir: Path = Path(
        os.getenv(
            "PROCESSED_DIR",
            PROCESSED_DIR.as_posix(),
        )
    )
    huggingface_model: str = os.getenv(
        "HUGGINGFACE_MODEL",
        "distilbert-base-uncased-finetuned-sst-2-english",
    )
    trend_window_days: int = int(os.getenv("TREND_WINDOW_DAYS", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    settings.ticket_raw_path.parent.mkdir(parents=True, exist_ok=True)
    settings.telemetry_raw_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


