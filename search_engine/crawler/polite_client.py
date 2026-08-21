"""Polite HTTP client with robots.txt checks for the Pure Portal crawler."""

from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from search_engine.config import SearchEngineConfig


class RobotsBlockedError(RuntimeError):
    """Raised when robots.txt disallows a URL."""


class FetchError(RuntimeError):
    """Raised when a URL cannot be fetched successfully."""


@dataclass
class FetchResult:
    url: str
    html: str
    status_code: int


class PoliteHttpClient:
    """Fetch pages while respecting domain limits, robots.txt, and crawl delay."""

    def __init__(self, config: SearchEngineConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
        self.robot_parser = self._load_robot_parser(config.seed_url)
        self.last_request_at = 0.0

    def _load_robot_parser(self, seed_url: str) -> RobotFileParser | None:
        parsed = urlparse(seed_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = self.session.get(
                robots_url,
                timeout=self.config.request_timeout_seconds,
            )
            if response.status_code >= 400:
                return None
            parser.parse(response.text.splitlines())
            return parser
        except requests.RequestException:
            return None

    def is_allowed_domain(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.netloc.endswith(
            self.config.allowed_domain
        )

    def can_fetch(self, url: str) -> bool:
        if not self.is_allowed_domain(url):
            return False
        if self.robot_parser is None:
            return True
        return self.robot_parser.can_fetch(self.config.user_agent, url)

    def _crawl_delay(self) -> float:
        if self.robot_parser is None:
            return self.config.crawl_delay_seconds
        robots_delay = self.robot_parser.crawl_delay(self.config.user_agent)
        return float(robots_delay or self.config.crawl_delay_seconds)

    def _wait_if_needed(self) -> None:
        delay = self._crawl_delay()
        elapsed = time.monotonic() - self.last_request_at
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def fetch(self, url: str) -> FetchResult:
        if not self.can_fetch(url):
            raise RobotsBlockedError(f"robots.txt disallowed URL: {url}")

        self._wait_if_needed()
        try:
            response = self.session.get(
                url,
                timeout=self.config.request_timeout_seconds,
            )
            self.last_request_at = time.monotonic()
            response.raise_for_status()
        except requests.RequestException as exc:
            raise FetchError(f"failed to fetch {url}: {exc}") from exc

        return FetchResult(
            url=response.url,
            html=response.text,
            status_code=response.status_code,
        )
