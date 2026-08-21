"""Repository methods for reading and saving crawled records in MongoDB."""

from __future__ import annotations

import re

from pymongo.database import Database

from search_engine.indexer.inverted_index import IndexBuildResult
from search_engine.indexer.ranking import rank_document_vectors
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

    def count_publications(self) -> int:
        return self.db.publications.count_documents({})

    def count_authors(self) -> int:
        return self.db.authors.count_documents({})

    def count_crawl_runs(self) -> int:
        return self.db.crawl_runs.count_documents({})

    def list_publications(
        self,
        year: int | None = None,
        author_query: str | None = None,
        text_query: str | None = None,
        sort_by: str = "newest",
        limit: int = 50,
    ) -> list[dict]:
        filters: dict = {}
        if year is not None:
            filters["publication_year"] = year

        and_filters = []
        if author_query:
            and_filters.append({"authors.name": {"$regex": re.escape(author_query), "$options": "i"}})
        if text_query:
            escaped_text_query = re.escape(text_query)
            and_filters.append(
                {
                    "$or": [
                        {"title": {"$regex": escaped_text_query, "$options": "i"}},
                        {"source": {"$regex": escaped_text_query, "$options": "i"}},
                        {"publication_type": {"$regex": escaped_text_query, "$options": "i"}},
                    ]
                }
            )
        if and_filters:
            filters["$and"] = and_filters

        sort_options = {
            "newest": [("publication_year", -1), ("title", 1)],
            "oldest": [("publication_year", 1), ("title", 1)],
            "title": [("title", 1)],
            "recently crawled": [("updated_at", -1)],
        }
        sort_fields = sort_options.get(sort_by, sort_options["newest"])

        cursor = (
            self.db.publications.find(filters, {"searchable_text": 0, "full_text": 0})
            .sort(sort_fields)
            .limit(limit)
        )
        return list(cursor)

    def list_available_years(self) -> list[int]:
        years = self.db.publications.distinct("publication_year")
        return sorted((year for year in years if isinstance(year, int)), reverse=True)

    def list_authors(self, limit: int = 100) -> list[dict]:
        cursor = (
            self.db.authors.find({})
            .sort([("name", 1)])
            .limit(limit)
        )
        return list(cursor)

    def list_crawl_runs(self, limit: int = 10) -> list[dict]:
        cursor = (
            self.db.crawl_runs.find({})
            .sort([("finished_at", -1)])
            .limit(limit)
        )
        return list(cursor)

    def list_publications_for_index(self) -> list[dict]:
        cursor = self.db.publications.find(
            {},
            {
                "_id": 0,
                "publication_key": 1,
                "title": 1,
                "publication_url": 1,
                "authors": 1,
                "publication_year": 1,
                "source": 1,
                "publication_type": 1,
                "abstract": 1,
                "searchable_text": 1,
            },
        )
        return list(cursor)


class IndexRepository:
    """MongoDB repository for custom inverted index and TF-IDF vectors."""

    INDEX_NAME = "publication_index"

    def __init__(self, db: Database):
        self.db = db
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        self.db.inverted_index.create_index("term", unique=True)
        self.db.document_vectors.create_index("publication_key", unique=True)
        self.db.index_metadata.create_index("name", unique=True)

    def save_index(self, index_result: IndexBuildResult) -> None:
        self.db.inverted_index.delete_many({})
        self.db.document_vectors.delete_many({})

        if index_result.inverted_index:
            self.db.inverted_index.insert_many(list(index_result.inverted_index.values()))
        if index_result.document_vectors:
            self.db.document_vectors.insert_many(index_result.document_vectors)

        self.db.index_metadata.update_one(
            {"name": self.INDEX_NAME},
            {
                "$set": {
                    "name": self.INDEX_NAME,
                    "document_count": index_result.document_count,
                    "vocabulary_size": index_result.vocabulary_size,
                    "indexed_at": utc_now(),
                }
            },
            upsert=True,
        )

    def get_index_metadata(self) -> dict | None:
        return self.db.index_metadata.find_one({"name": self.INDEX_NAME}, {"_id": 0})

    def count_terms(self) -> int:
        return self.db.inverted_index.count_documents({})

    def count_document_vectors(self) -> int:
        return self.db.document_vectors.count_documents({})

    def get_idf_weights(self) -> dict[str, float]:
        cursor = self.db.inverted_index.find({}, {"_id": 0, "term": 1, "idf": 1})
        return {document["term"]: float(document["idf"]) for document in cursor}

    def list_document_vectors(self) -> list[dict]:
        cursor = self.db.document_vectors.find(
            {},
            {
                "_id": 0,
                "publication_key": 1,
                "title": 1,
                "publication_url": 1,
                "publication_year": 1,
                "authors": 1,
                "vector": 1,
            },
        )
        return list(cursor)

    def find_publications_by_keys(self, publication_keys: list[str]) -> dict[str, dict]:
        if not publication_keys:
            return {}

        cursor = self.db.publications.find(
            {"publication_key": {"$in": publication_keys}},
            {"searchable_text": 0, "full_text": 0},
        )
        return {document["publication_key"]: document for document in cursor}

    def search(self, query: str, limit: int = 10) -> list[dict]:
        idf_weights = self.get_idf_weights()
        document_vectors = self.list_document_vectors()
        ranked_matches = rank_document_vectors(query, document_vectors, idf_weights, limit=limit)
        publications_by_key = self.find_publications_by_keys(
            [match["publication_key"] for match in ranked_matches]
        )

        results = []
        for match in ranked_matches:
            publication = publications_by_key.get(match["publication_key"])
            if not publication:
                continue
            results.append(
                {
                    **publication,
                    "score": match["score"],
                    "matched_terms": match["matched_terms"],
                    "query_tokens": match["query_tokens"],
                }
            )
        return results
