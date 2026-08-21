"""Text preprocessing used by both indexing and user queries."""

from __future__ import annotations

import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def clean_and_tokenize(text: str) -> list[str]:
    """Lowercase text, remove punctuation, and split into word tokens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()


def remove_stop_words(tokens: list[str]) -> list[str]:
    """Remove common English stop words and very short terms."""
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 2]


def stem_token(token: str) -> str:
    """Apply a small rule-based stemmer suitable for coursework demonstrations."""
    if len(token) <= 4:
        return token

    suffix_rules = (
        ("ization", "ize"),
        ("ational", "ate"),
        ("fulness", "ful"),
        ("ousness", "ous"),
        ("iveness", "ive"),
        ("tional", "tion"),
        ("ments", "ment"),
        ("ingly", ""),
        ("edly", ""),
        ("ies", "y"),
        ("ing", ""),
        ("ed", ""),
        ("es", ""),
        ("s", ""),
    )

    for suffix, replacement in suffix_rules:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)] + replacement

    return token


def stem_tokens(tokens: list[str]) -> list[str]:
    return [stem_token(token) for token in tokens]


def preprocess_text(text: str) -> list[str]:
    """Return normalized tokens for indexing and ranked retrieval."""
    tokens = clean_and_tokenize(text)
    tokens = remove_stop_words(tokens)
    return stem_tokens(tokens)


def preprocess_with_positions(text: str) -> list[tuple[str, int]]:
    """Return preprocessed terms with positions after filtering."""
    return [(token, position) for position, token in enumerate(preprocess_text(text))]
