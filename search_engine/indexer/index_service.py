"""Shared service for rebuilding the stored publication index."""

from __future__ import annotations

from pymongo.database import Database

from search_engine.database.repositories import IndexRepository, PublicationRepository
from search_engine.indexer.inverted_index import build_publication_index


def rebuild_publication_index(db: Database) -> str:
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
