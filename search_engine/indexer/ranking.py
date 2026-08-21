"""Ranked retrieval using TF-IDF vectors and cosine similarity."""

from __future__ import annotations

from collections import Counter
from typing import Any

from search_engine.indexer.inverted_index import normalize_vector, sublinear_tf
from search_engine.indexer.preprocessing import preprocess_text


def dot_product(first: dict[str, float], second: dict[str, float]) -> float:
    if len(first) > len(second):
        first, second = second, first
    return sum(weight * second.get(term, 0.0) for term, weight in first.items())


def cosine_similarity(first: dict[str, float], second: dict[str, float]) -> float:
    return dot_product(first, second)


def build_query_vector(query: str, idf_weights: dict[str, float]) -> tuple[dict[str, float], list[str]]:
    query_tokens = preprocess_text(query)
    query_counts = Counter(query_tokens)
    raw_vector = {
        term: sublinear_tf(frequency) * idf_weights.get(term, 0.0)
        for term, frequency in query_counts.items()
        if term in idf_weights
    }
    return normalize_vector(raw_vector), query_tokens


def rank_document_vectors(
    query: str,
    document_vectors: list[dict[str, Any]],
    idf_weights: dict[str, float],
    limit: int = 10,
) -> list[dict[str, Any]]:
    query_vector, query_tokens = build_query_vector(query, idf_weights)
    if not query_vector:
        return []

    query_terms = set(query_vector)
    results = []
    for document in document_vectors:
        document_vector = document.get("vector", {})
        score = cosine_similarity(query_vector, document_vector)
        if score <= 0:
            continue

        matched_terms = sorted(query_terms & set(document_vector))
        results.append(
            {
                "publication_key": document["publication_key"],
                "score": score,
                "matched_terms": matched_terms,
                "query_tokens": query_tokens,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]
