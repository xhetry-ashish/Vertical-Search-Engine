"""TF-IDF document clustering with K-Means implemented from scratch."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from search_engine.indexer.preprocessing import preprocess_text


@dataclass
class ClusteringResult:
    documents: list[dict]
    vocabulary: list[str]
    idf_weights: dict[str, float]
    matrix: np.ndarray
    labels: np.ndarray
    centroids: np.ndarray
    cluster_summaries: list[dict]
    iterations: int


def build_tfidf_matrix(documents: list[dict]) -> tuple[np.ndarray, list[str], dict[str, float]]:
    tokenized_documents = [preprocess_text(document["text"]) for document in documents]
    vocabulary = sorted({token for tokens in tokenized_documents for token in tokens})
    term_to_index = {term: index for index, term in enumerate(vocabulary)}
    document_count = len(tokenized_documents)

    document_frequency = Counter()
    for tokens in tokenized_documents:
        for term in set(tokens):
            document_frequency[term] += 1

    idf_weights = {
        term: math.log10((document_count + 1) / (frequency + 1)) + 1
        for term, frequency in document_frequency.items()
    }

    matrix = np.zeros((document_count, len(vocabulary)), dtype=float)
    for row_index, tokens in enumerate(tokenized_documents):
        term_counts = Counter(tokens)
        for term, frequency in term_counts.items():
            column_index = term_to_index[term]
            tf_weight = 1 + math.log10(frequency)
            matrix[row_index, column_index] = tf_weight * idf_weights[term]

    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1
    matrix = matrix / norms[:, None]
    return matrix, vocabulary, idf_weights


def fit_kmeans(
    matrix: np.ndarray,
    n_clusters: int = 3,
    random_state: int = 42,
    max_iter: int = 100,
) -> tuple[np.ndarray, np.ndarray, int]:
    if n_clusters <= 0:
        raise ValueError("n_clusters must be greater than zero.")
    if n_clusters > len(matrix):
        raise ValueError("n_clusters cannot exceed the number of documents.")

    rng = np.random.default_rng(random_state)
    initial_indices = rng.choice(len(matrix), size=n_clusters, replace=False)
    centroids = matrix[initial_indices].copy()
    labels = np.full(len(matrix), -1, dtype=int)

    for iteration in range(1, max_iter + 1):
        distances = np.linalg.norm(matrix[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = distances.argmin(axis=1)

        new_centroids = centroids.copy()
        for cluster_id in range(n_clusters):
            members = matrix[new_labels == cluster_id]
            if len(members) > 0:
                new_centroids[cluster_id] = members.mean(axis=0)

        if np.array_equal(labels, new_labels):
            return new_labels, new_centroids, iteration

        labels = new_labels
        centroids = new_centroids

    return labels, centroids, max_iter


def top_terms_for_cluster(
    centroid: np.ndarray,
    vocabulary: list[str],
    limit: int = 8,
) -> list[str]:
    if len(vocabulary) == 0:
        return []

    top_indices = np.argsort(centroid)[::-1][:limit]
    return [vocabulary[index] for index in top_indices if centroid[index] > 0]


def summarize_clusters(
    documents: list[dict],
    labels: np.ndarray,
    centroids: np.ndarray,
    vocabulary: list[str],
) -> list[dict]:
    category_counts_by_cluster: dict[int, Counter] = defaultdict(Counter)
    for document, label in zip(documents, labels):
        category_counts_by_cluster[int(label)][document["category"]] += 1

    summaries = []
    for cluster_id in range(len(centroids)):
        category_counts = category_counts_by_cluster[cluster_id]
        majority_category = category_counts.most_common(1)[0][0] if category_counts else "Unknown"
        summaries.append(
            {
                "cluster": cluster_id,
                "documents": int(sum(category_counts.values())),
                "majority_category": majority_category,
                "category_counts": dict(category_counts),
                "top_terms": top_terms_for_cluster(centroids[cluster_id], vocabulary),
            }
        )
    return summaries


def fit_clustering_model(
    documents: list[dict],
    n_clusters: int = 3,
    random_state: int = 42,
    max_iter: int = 100,
) -> ClusteringResult:
    matrix, vocabulary, idf_weights = build_tfidf_matrix(documents)
    labels, centroids, iterations = fit_kmeans(
        matrix=matrix,
        n_clusters=n_clusters,
        random_state=random_state,
        max_iter=max_iter,
    )
    cluster_summaries = summarize_clusters(documents, labels, centroids, vocabulary)
    return ClusteringResult(
        documents=documents,
        vocabulary=vocabulary,
        idf_weights=idf_weights,
        matrix=matrix,
        labels=labels,
        centroids=centroids,
        cluster_summaries=cluster_summaries,
        iterations=iterations,
    )


def vectorize_text(text: str, vocabulary: list[str], idf_weights: dict[str, float]) -> np.ndarray:
    term_to_index = {term: index for index, term in enumerate(vocabulary)}
    vector = np.zeros(len(vocabulary), dtype=float)
    term_counts = Counter(preprocess_text(text))

    for term, frequency in term_counts.items():
        if term not in term_to_index:
            continue
        vector[term_to_index[term]] = (1 + math.log10(frequency)) * idf_weights.get(term, 0.0)

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


def predict_cluster(text: str, result: ClusteringResult) -> dict[str, Any]:
    vector = vectorize_text(text, result.vocabulary, result.idf_weights)
    if np.linalg.norm(vector) == 0:
        return {
            "cluster": None,
            "majority_category": "Unknown",
            "distance": None,
            "top_terms": [],
        }

    distances = np.linalg.norm(result.centroids - vector, axis=1)
    cluster_id = int(distances.argmin())
    summary = result.cluster_summaries[cluster_id]
    return {
        "cluster": cluster_id,
        "majority_category": summary["majority_category"],
        "distance": float(distances[cluster_id]),
        "top_terms": summary["top_terms"],
    }
