"""Data models for crawled authors, publications, and crawl runs."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


@dataclass
class Author:
    name: str
    profile_url: str | None = None
    affiliation: str | None = None

    @property
    def author_key(self) -> str:
        if self.profile_url:
            return stable_id(self.profile_url)
        return stable_id(normalize_name(self.name).lower())

    def to_mongo(self) -> dict:
        data = asdict(self)
        data["author_key"] = self.author_key
        return data


@dataclass
class Publication:
    title: str
    publication_url: str
    authors: list[Author] = field(default_factory=list)
    publication_year: int | None = None
    published_date: str | None = None
    source: str | None = None
    publication_type: str | None = None
    abstract: str | None = None
    full_text: str = ""
    crawled_from: str | None = None
    crawled_at: datetime = field(default_factory=utc_now)

    @property
    def publication_key(self) -> str:
        return stable_id(self.publication_url)

    def searchable_text(self) -> str:
        author_names = " ".join(author.name for author in self.authors)
        parts = [
            self.title,
            author_names,
            str(self.publication_year or ""),
            self.source or "",
            self.publication_type or "",
            self.abstract or "",
            self.full_text,
        ]
        return " ".join(part for part in parts if part).strip()

    def to_mongo(self) -> dict:
        data = asdict(self)
        data["publication_key"] = self.publication_key
        data["author_keys"] = [author.author_key for author in self.authors]
        data["searchable_text"] = self.searchable_text()
        return data


@dataclass
class CrawlRun:
    seed_url: str
    pages_visited: int
    publications_found: int
    publications_saved: int
    skipped_by_robots: list[str] = field(default_factory=list)
    failed_urls: list[dict] = field(default_factory=list)
    status: str = "completed"
    started_at: datetime = field(default_factory=utc_now)
    finished_at: datetime = field(default_factory=utc_now)

    def to_mongo(self) -> dict:
        return asdict(self)
