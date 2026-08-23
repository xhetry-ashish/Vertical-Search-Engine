"""Project configuration loaded from environment variables or a local .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_URL = (
    "https://pureportal.coventry.ac.uk/en/organisations/"
    "centre-for-healthcare-and-community-transformation/"
)


def load_dotenv(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs from .env without requiring python-dotenv."""
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class SearchEngineConfig:
    seed_url: str
    allowed_domain: str
    user_agent: str
    crawl_delay_seconds: float
    request_timeout_seconds: int
    max_listing_pages: int
    max_profile_pages: int
    max_publications: int
    scheduler_interval_days: int
    mongo_uri: str | None
    mongo_db_name: str

    @classmethod
    def from_env(cls) -> "SearchEngineConfig":
        load_dotenv()
        return cls(
            seed_url=os.environ.get("PUREPORTAL_SEED_URL", DEFAULT_SEED_URL),
            allowed_domain=os.environ.get("ALLOWED_DOMAIN", "pureportal.coventry.ac.uk"),
            user_agent=os.environ.get(
                "USER_AGENT",
                "SoftwaricaIRSearchEngine/1.0 (student coursework crawler)",
            ),
            crawl_delay_seconds=_get_float("CRAWL_DELAY_SECONDS", 2.0),
            request_timeout_seconds=_get_int("REQUEST_TIMEOUT_SECONDS", 20),
            max_listing_pages=_get_int("MAX_LISTING_PAGES", 5),
            max_profile_pages=_get_int("MAX_PROFILE_PAGES", 10),
            max_publications=_get_int("MAX_PUBLICATIONS", 25),
            scheduler_interval_days=_get_int("SCHEDULER_INTERVAL_DAYS", 7),
            mongo_uri=os.environ.get("MONGO_URI"),
            mongo_db_name=os.environ.get("MONGO_DB_NAME", "ir_vertical_search_engine"),
        )
