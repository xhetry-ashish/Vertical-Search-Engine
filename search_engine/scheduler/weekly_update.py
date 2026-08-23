"""Weekly crawler/index update scheduler."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from search_engine.config import SearchEngineConfig
from search_engine.crawler.pureportal_crawler import PurePortalCrawler
from search_engine.database.mongo import MongoConnection
from search_engine.database.repositories import PublicationRepository
from search_engine.indexer.index_service import rebuild_publication_index


SECONDS_PER_DAY = 24 * 60 * 60


@dataclass
class ScheduledUpdateResult:
    started_at: datetime
    finished_at: datetime
    publications_extracted: int
    publications_saved: int
    pages_visited: int
    profile_pages_visited: int
    crawl_run_id: str
    index_message: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def interval_days_to_seconds(interval_days: float) -> int:
    if interval_days <= 0:
        raise ValueError("Scheduler interval must be greater than zero days.")
    return max(1, int(interval_days * SECONDS_PER_DAY))


def run_update_once(
    config: SearchEngineConfig | None = None,
    max_listing_pages: int | None = None,
    max_profile_pages: int | None = None,
    max_publications: int | None = None,
) -> ScheduledUpdateResult:
    """Run one scheduled update: crawl, save records, and rebuild the index."""
    config = config or SearchEngineConfig.from_env()
    started_at = utc_now()

    connection = MongoConnection(config)
    try:
        connection.ping()
        crawler = PurePortalCrawler(config)
        crawl_output = crawler.crawl_publications(
            max_listing_pages=max_listing_pages,
            max_profile_pages=max_profile_pages,
            max_publications=max_publications,
        )
        publication_repository = PublicationRepository(connection.db)
        saved_count = publication_repository.save_publications(crawl_output.publications)
        crawl_run = crawler.build_crawl_run(crawl_output, publications_saved=saved_count)
        crawl_run_id = publication_repository.save_crawl_run(crawl_run)
        index_message = rebuild_publication_index(connection.db)
    finally:
        connection.close()

    result = ScheduledUpdateResult(
        started_at=started_at,
        finished_at=utc_now(),
        publications_extracted=len(crawl_output.publications),
        publications_saved=saved_count,
        pages_visited=crawl_output.pages_visited,
        profile_pages_visited=crawl_output.profile_pages_visited,
        crawl_run_id=crawl_run_id,
        index_message=index_message,
    )
    logging.info(
        "Scheduled update completed: extracted=%s saved=%s pages=%s %s",
        result.publications_extracted,
        result.publications_saved,
        result.pages_visited,
        result.index_message,
    )
    return result


def run_scheduler(
    config: SearchEngineConfig | None = None,
    interval_days: float | None = None,
    max_listing_pages: int | None = None,
    max_profile_pages: int | None = None,
    max_publications: int | None = None,
    run_immediately: bool = True,
) -> None:
    """Run scheduled updates forever using a simple weekly sleep loop."""
    config = config or SearchEngineConfig.from_env()
    interval_days = interval_days or config.scheduler_interval_days
    wait_seconds = interval_days_to_seconds(interval_days)

    logging.info("Scheduler started. Interval: %s days.", interval_days)

    if run_immediately:
        run_update_once(
            config=config,
            max_listing_pages=max_listing_pages,
            max_profile_pages=max_profile_pages,
            max_publications=max_publications,
        )

    while True:
        logging.info("Next scheduled update in %s seconds.", wait_seconds)
        time.sleep(wait_seconds)
        run_update_once(
            config=config,
            max_listing_pages=max_listing_pages,
            max_profile_pages=max_profile_pages,
            max_publications=max_publications,
        )
