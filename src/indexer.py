"""Core inverted-index utilities for the coursework search tool."""

from __future__ import annotations

import re
from typing import Any


WORD_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def normalize_text(text: str) -> str:
    """Return lowercase text so indexing and search are case-insensitive."""
    return text.lower()


def tokenize(text: str) -> list[str]:
    """Extract normalized words from text.

    The regex keeps simple apostrophes inside words such as "don't" while
    ignoring surrounding punctuation.
    """

    normalized_text = normalize_text(text)
    return WORD_PATTERN.findall(normalized_text)


def build_page_entry(page: dict[str, Any]) -> dict[str, str]:
    """Extract the page metadata we want to keep alongside the index."""

    return {
        "title": page.get("title", ""),
    }


def build_inverted_index(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an inverted index from a list of crawled pages.

    Each page is expected to provide at least:
    - "url": the page URL
    - "text": the visible text to index
    - "title": optional page title metadata
    """

    page_metadata: dict[str, dict[str, str]] = {}
    inverted_index: dict[str, dict[str, dict[str, Any]]] = {}

    for page in pages:
        url = page["url"]
        tokens = tokenize(page.get("text", ""))
        page_metadata[url] = build_page_entry(page)

        for position, word in enumerate(tokens):
            word_entry = inverted_index.setdefault(word, {})
            page_entry = word_entry.setdefault(
                url,
                {"frequency": 0, "positions": []},
            )
            page_entry["frequency"] += 1
            page_entry["positions"].append(position)

    return {
        "pages": page_metadata,
        "inverted_index": inverted_index,
    }


def get_word_entry(index_data: dict[str, Any], word: str) -> dict[str, Any]:
    """Return the posting list for a word after normalizing its case."""

    normalized_word = normalize_text(word).strip()
    return index_data.get("inverted_index", {}).get(normalized_word, {})
