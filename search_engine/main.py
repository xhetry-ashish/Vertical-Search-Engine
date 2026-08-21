"""Command-line runner for crawling, indexing, and searching publications."""

from __future__ import annotations

import argparse
import logging
import sys

from search_engine.config import SearchEngineConfig
from search_engine.crawler.pureportal_crawler import PurePortalCrawler
from search_engine.database.mongo import MongoConnection
from search_engine.database.repositories import IndexRepository, PublicationRepository
from search_engine.indexer.inverted_index import build_publication_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crawl Coventry Pure Portal publications and store them in MongoDB."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Run steps 1 to 3: crawl, extract metadata, and save records.",
    )
    crawl_parser.add_argument("--max-listing-pages", type=int, default=None)
    crawl_parser.add_argument("--max-publications", type=int, default=None)
    crawl_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl and extract records, but do not write to MongoDB.",
    )
    crawl_parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Save crawled records without rebuilding the search index.",
    )

    subparsers.add_parser("check-db", help="Check MongoDB connection.")

    subparsers.add_parser(
        "build-index",
        help="Build the custom inverted index and TF-IDF vectors from MongoDB publications.",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Run ranked publication search against the stored index.",
    )
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    return parser


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def run_crawl(args: argparse.Namespace) -> int:
    config = SearchEngineConfig.from_env()
    crawler = PurePortalCrawler(config)
    output = crawler.crawl_publications(
        max_listing_pages=args.max_listing_pages,
        max_publications=args.max_publications,
    )

    print(f"Publication records extracted: {len(output.publications)}")
    print(f"Listing pages visited: {output.pages_visited}")
    if output.skipped_by_robots:
        print(f"URLs skipped by robots.txt: {len(output.skipped_by_robots)}")
    if output.failed_urls:
        print(f"Failed URLs: {len(output.failed_urls)}")

    if args.dry_run:
        for publication in output.publications[:5]:
            print()
            print(publication.title)
            print(publication.publication_url)
            print("Authors:", ", ".join(author.name for author in publication.authors) or "Unknown")
            print("Year:", publication.publication_year or "Unknown")
        return 0

    connection = MongoConnection(config)
    try:
        connection.ping()
        repository = PublicationRepository(connection.db)
        saved_count = repository.save_publications(output.publications)
        crawl_run = crawler.build_crawl_run(output, publications_saved=saved_count)
        crawl_run_id = repository.save_crawl_run(crawl_run)

        index_message = "Index rebuild skipped."
        if not args.skip_index:
            index_message = rebuild_index(connection.db)
    finally:
        connection.close()

    print(f"Publication records saved or updated: {saved_count}")
    print(f"Crawl run saved with id: {crawl_run_id}")
    print(index_message)
    return 0


def rebuild_index(db) -> str:
    publication_repository = PublicationRepository(db)
    index_repository = IndexRepository(db)
    publications = publication_repository.list_publications_for_index()
    index_result = build_publication_index(publications)
    index_repository.save_index(index_result)
    return (
        "Index rebuilt: "
        f"{index_result.document_count} documents, "
        f"{index_result.vocabulary_size} terms."
    )


def run_build_index() -> int:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        print(rebuild_index(connection.db))
    finally:
        connection.close()
    return 0


def run_search(args: argparse.Namespace) -> int:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        index_repository = IndexRepository(connection.db)
        results = index_repository.search(args.query, limit=args.limit)
    finally:
        connection.close()

    if not results:
        print("No ranked results found. Build the index first or try a different query.")
        return 0

    for rank, publication in enumerate(results, 1):
        print()
        print(f"{rank}. {publication.get('title', 'Untitled')}")
        print(f"   Score: {publication.get('score', 0):.4f}")
        print(f"   Year: {publication.get('publication_year') or 'Unknown'}")
        print(f"   URL: {publication.get('publication_url') or 'No URL'}")
        print(f"   Matched terms: {', '.join(publication.get('matched_terms', []))}")
    return 0


def check_db() -> int:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
    finally:
        connection.close()

    print(f"MongoDB connection OK: database '{config.mongo_db_name}'")
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "crawl":
        return run_crawl(args)
    if args.command == "check-db":
        return check_db()
    if args.command == "build-index":
        return run_build_index()
    if args.command == "search":
        return run_search(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
