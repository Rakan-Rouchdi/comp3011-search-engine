"""Core inverted-index utilities for the coursework search tool."""

from __future__ import annotations

import json
import re
from pathlib import Path
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


def save_index(index_data: dict[str, Any], file_path: str | Path) -> None:
    """Save the full index data to a single JSON file."""

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(index_data, file_handle, indent=2)


def load_index(file_path: str | Path) -> dict[str, Any]:
    """Load index data from a JSON file on disk."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Index file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except json.JSONDecodeError as error:
        raise ValueError(f"Index file is not valid JSON: {path}") from error
