"""Repository methods for saving crawled records in MongoDB."""

from __future__ import annotations

from pymongo.database import Database

from search_engine.models import CrawlRun, Publication, utc_now


class PublicationRepository:
    """MongoDB repository for publications, authors, and crawl logs."""

    def __init__(self, db: Database):
        self.db = db
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        self.db.publications.create_index("publication_key", unique=True)
        self.db.publications.create_index("publication_url", unique=True)
        self.db.publications.create_index("publication_year")
        self.db.authors.create_index("author_key", unique=True)
        self.db.authors.create_index("profile_url")
        self.db.crawl_runs.create_index("finished_at")

    def save_authors(self, publication: Publication) -> int:
        changed = 0
        for author in publication.authors:
            document = author.to_mongo()
            document["updated_at"] = utc_now()
            result = self.db.authors.update_one(
                {"author_key": document["author_key"]},
                {
                    "$set": document,
                    "$setOnInsert": {"first_seen_at": utc_now()},
                    "$addToSet": {"publication_keys": publication.publication_key},
                },
                upsert=True,
            )
            if result.upserted_id or result.modified_count:
                changed += 1
        return changed

    def save_publication(self, publication: Publication) -> bool:
        self.save_authors(publication)

        document = publication.to_mongo()
        document["updated_at"] = utc_now()

        result = self.db.publications.update_one(
            {"publication_key": document["publication_key"]},
            {
                "$set": document,
                "$setOnInsert": {"first_seen_at": utc_now()},
            },
            upsert=True,
        )
        return bool(result.upserted_id or result.modified_count)

    def save_publications(self, publications: list[Publication]) -> int:
        saved = 0
        for publication in publications:
            if self.save_publication(publication):
                saved += 1
        return saved

    def save_crawl_run(self, crawl_run: CrawlRun) -> str:
        result = self.db.crawl_runs.insert_one(crawl_run.to_mongo())
        return str(result.inserted_id)
