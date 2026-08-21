"""Crawler for Coventry University Pure Portal publication records."""

from __future__ import annotations

import logging
from collections import OrderedDict, deque
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin, urlparse

from search_engine.config import SearchEngineConfig
from search_engine.crawler.parsers import (
    extract_listing_urls,
    merge_publication_data,
    parse_publication_page,
    parse_publication_summaries,
)
from search_engine.crawler.polite_client import FetchError, PoliteHttpClient, RobotsBlockedError
from search_engine.models import CrawlRun, Publication, utc_now


@dataclass
class CrawlerOutput:
    publications: list[Publication]
    pages_visited: int
    skipped_by_robots: list[str]
    failed_urls: list[dict]
    started_at: datetime
    finished_at: datetime


class PurePortalCrawler:
    """Crawl the centre's Pure Portal publication pages."""

    def __init__(self, config: SearchEngineConfig, client: PoliteHttpClient | None = None):
        self.config = config
        self.client = client or PoliteHttpClient(config)
        self.organisation_path = urlparse(config.seed_url).path.rstrip("/")
        seed_base = config.seed_url if config.seed_url.endswith("/") else f"{config.seed_url}/"
        self.publications_listing_url = urljoin(seed_base, "publications/")

    def crawl_publications(
        self,
        max_listing_pages: int | None = None,
        max_publications: int | None = None,
    ) -> CrawlerOutput:
        max_listing_pages = max_listing_pages or self.config.max_listing_pages
        max_publications = max_publications or self.config.max_publications
        started_at = utc_now()

        listing_queue = deque([self.config.seed_url])
        queued_listings = {self.config.seed_url}
        visited_listings: set[str] = set()
        skipped_by_robots: list[str] = []
        failed_urls: list[dict] = []
        summaries_by_url: OrderedDict[str, Publication] = OrderedDict()

        while listing_queue and len(visited_listings) < max_listing_pages:
            listing_url = listing_queue.popleft()
            if listing_url in visited_listings:
                continue

            try:
                result = self.client.fetch(listing_url)
            except RobotsBlockedError as exc:
                skipped_by_robots.append(listing_url)
                logging.info("%s", exc)
                continue
            except FetchError as exc:
                failed_urls.append({"url": listing_url, "error": str(exc)})
                logging.warning("%s", exc)
                continue

            visited_listings.add(listing_url)
            logging.info("Crawled listing page: %s", result.url)

            for publication in parse_publication_summaries(result.html, result.url):
                summaries_by_url.setdefault(publication.publication_url, publication)

            for discovered_url in extract_listing_urls(
                result.html,
                result.url,
                self.organisation_path,
            ):
                if discovered_url not in visited_listings and discovered_url not in queued_listings:
                    listing_queue.append(discovered_url)
                    queued_listings.add(discovered_url)

        selected_summaries = list(summaries_by_url.values())[:max_publications]
        publications: list[Publication] = []

        for summary in selected_summaries:
            try:
                result = self.client.fetch(summary.publication_url)
                detail = parse_publication_page(result.html, result.url)
                publications.append(merge_publication_data(summary, detail))
                logging.info("Crawled publication page: %s", result.url)
            except RobotsBlockedError as exc:
                skipped_by_robots.append(summary.publication_url)
                publications.append(summary)
                logging.info("%s", exc)
            except FetchError as exc:
                failed_urls.append({"url": summary.publication_url, "error": str(exc)})
                publications.append(summary)
                logging.warning("%s", exc)

        return CrawlerOutput(
            publications=publications,
            pages_visited=len(visited_listings),
            skipped_by_robots=skipped_by_robots,
            failed_urls=failed_urls,
            started_at=started_at,
            finished_at=utc_now(),
        )

    def build_crawl_run(self, output: CrawlerOutput, publications_saved: int) -> CrawlRun:
        return CrawlRun(
            seed_url=self.config.seed_url,
            pages_visited=output.pages_visited,
            publications_found=len(output.publications),
            publications_saved=publications_saved,
            skipped_by_robots=output.skipped_by_robots,
            failed_urls=output.failed_urls,
            status="completed",
            started_at=output.started_at,
            finished_at=output.finished_at,
        )
