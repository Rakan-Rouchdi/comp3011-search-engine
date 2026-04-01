"""Search helpers for querying the inverted index."""

from __future__ import annotations

from typing import Any

from src.indexer import get_word_entry, tokenize


def normalize_query(query: str) -> list[str]:
    """Convert a query string into normalized tokens."""

    return tokenize(query.strip())


def search_word(index_data: dict[str, Any], word: str) -> list[str]:
    """Return URLs of pages that contain a single word."""

    return sorted(get_word_entry(index_data, word).keys())


def page_contains_phrase(
    inverted_index: dict[str, Any], url: str, query_words: list[str]
) -> bool:
    """Check whether a page contains the full query phrase in order."""

    if not query_words:
        return False

    first_word_positions = inverted_index[query_words[0]][url]["positions"]

    for start_position in first_word_positions:
        matches_phrase = True

        for offset, word in enumerate(query_words[1:], start=1):
            positions = inverted_index[word][url]["positions"]
            if start_position + offset not in positions:
                matches_phrase = False
                break

        if matches_phrase:
            return True

    return False


def search_phrase(index_data: dict[str, Any], query: str) -> list[str]:
    """Return URLs of pages that contain an exact multi-word phrase."""

    query_words = normalize_query(query)
    if not query_words:
        return []

    if len(query_words) == 1:
        return search_word(index_data, query_words[0])

    inverted_index = index_data.get("inverted_index", {})
    if any(word not in inverted_index for word in query_words):
        return []

    candidate_pages = set(inverted_index[query_words[0]].keys())
    for word in query_words[1:]:
        candidate_pages &= set(inverted_index[word].keys())

    matches = [
        url
        for url in sorted(candidate_pages)
        if page_contains_phrase(inverted_index, url, query_words)
    ]
    return matches


def search_all_words(index_data: dict[str, Any], query: str) -> list[str]:
    """Return URLs of pages that contain every word in the query."""

    query_words = normalize_query(query)
    if not query_words:
        return []

    inverted_index = index_data.get("inverted_index", {})
    if any(word not in inverted_index for word in query_words):
        return []

    matching_pages = set(inverted_index[query_words[0]].keys())
    for word in query_words[1:]:
        matching_pages &= set(inverted_index[word].keys())

    return sorted(matching_pages)


def find_query(index_data: dict[str, Any], query: str) -> list[str]:
    """Search for pages containing the query word or all query words."""

    query_words = normalize_query(query)
    if not query_words:
        return []

    if len(query_words) == 1:
        return search_word(index_data, query_words[0])

    return search_all_words(index_data, query)
