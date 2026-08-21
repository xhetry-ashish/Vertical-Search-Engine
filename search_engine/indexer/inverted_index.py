"""Inverted index and TF-IDF vector construction."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from search_engine.indexer.preprocessing import preprocess_text
from search_engine.models import utc_now


@dataclass
class IndexBuildResult:
    document_count: int
    vocabulary_size: int
    inverted_index: dict[str, dict]
    document_vectors: list[dict]
    idf_weights: dict[str, float]


def term_frequency(term: str, tokens: list[str]) -> int:
    return tokens.count(term)


def sublinear_tf(frequency: int) -> float:
    if frequency <= 0:
        return 0.0
    return 1.0 + math.log10(frequency)


def inverse_document_frequency(total_documents: int, document_frequency: int) -> float:
    if total_documents <= 0 or document_frequency <= 0:
        return 0.0
    return math.log10((total_documents + 1) / (document_frequency + 1)) + 1.0


def vector_magnitude(vector: dict[str, float]) -> float:
    return math.sqrt(sum(weight * weight for weight in vector.values()))


def normalize_vector(vector: dict[str, float]) -> dict[str, float]:
    magnitude = vector_magnitude(vector)
    if magnitude == 0:
        return {}
    return {term: weight / magnitude for term, weight in vector.items()}


def publication_search_text(publication: dict[str, Any]) -> str:
    author_names = " ".join(
        author.get("name", "")
        for author in publication.get("authors", [])
        if isinstance(author, dict)
    )
    parts = [
        publication.get("title", ""),
        author_names,
        str(publication.get("publication_year") or ""),
        publication.get("source", ""),
        publication.get("publication_type", ""),
        publication.get("abstract", ""),
        publication.get("searchable_text", ""),
    ]
    return " ".join(part for part in parts if part).strip()


def build_publication_index(publications: list[dict[str, Any]]) -> IndexBuildResult:
    """Build an inverted index and normalized TF-IDF vectors from publications."""
    tokenized_documents: dict[str, list[str]] = {}
    document_metadata: dict[str, dict] = {}
    positions_by_document: dict[str, dict[str, list[int]]] = {}
    document_frequency: Counter[str] = Counter()

    for publication in publications:
        publication_key = publication["publication_key"]
        tokens = preprocess_text(publication_search_text(publication))
        tokenized_documents[publication_key] = tokens
        document_metadata[publication_key] = {
            "publication_key": publication_key,
            "title": publication.get("title", ""),
            "publication_url": publication.get("publication_url", ""),
            "publication_year": publication.get("publication_year"),
            "authors": publication.get("authors", []),
        }

        positions: dict[str, list[int]] = defaultdict(list)
        for position, token in enumerate(tokens):
            positions[token].append(position)
        positions_by_document[publication_key] = dict(positions)

        for term in set(tokens):
            document_frequency[term] += 1

    total_documents = len(tokenized_documents)
    idf_weights = {
        term: inverse_document_frequency(total_documents, frequency)
        for term, frequency in document_frequency.items()
    }

    inverted_index: dict[str, dict] = {}
    for term in sorted(document_frequency):
        postings = []
        for publication_key, positions in positions_by_document.items():
            term_positions = positions.get(term)
            if not term_positions:
                continue
            postings.append(
                {
                    "publication_key": publication_key,
                    "term_frequency": len(term_positions),
                    "positions": term_positions,
                }
            )

        inverted_index[term] = {
            "term": term,
            "document_frequency": document_frequency[term],
            "idf": idf_weights[term],
            "postings": postings,
        }

    document_vectors = []
    indexed_at = utc_now()
    for publication_key, tokens in tokenized_documents.items():
        term_counts = Counter(tokens)
        raw_vector = {
            term: sublinear_tf(frequency) * idf_weights.get(term, 0.0)
            for term, frequency in term_counts.items()
        }
        vector = normalize_vector(raw_vector)
        metadata = document_metadata[publication_key]
        document_vectors.append(
            {
                **metadata,
                "token_count": len(tokens),
                "unique_term_count": len(term_counts),
                "vector": vector,
                "indexed_at": indexed_at,
            }
        )

    return IndexBuildResult(
        document_count=total_documents,
        vocabulary_size=len(inverted_index),
        inverted_index=inverted_index,
        document_vectors=document_vectors,
        idf_weights=idf_weights,
    )
