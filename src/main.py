"""Workflow helpers for building and loading the coursework search index."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.crawler import DEFAULT_BASE_URL, crawl_site
from src.indexer import build_inverted_index, load_index, save_index


DEFAULT_INDEX_PATH = Path("data/index.json")


def build_search_index(
    *,
    base_url: str = DEFAULT_BASE_URL,
    output_path: str | Path = DEFAULT_INDEX_PATH,
    crawl_func: Callable[..., list[dict[str, Any]]] = crawl_site,
) -> dict[str, Any]:
    """Crawl the target site, build the index, and save it to disk."""

    pages = crawl_func(base_url=base_url)
    index_data = build_inverted_index(pages)
    index_data["base_url"] = base_url
    save_index(index_data, output_path)
    return index_data


def load_saved_index(file_path: str | Path = DEFAULT_INDEX_PATH) -> dict[str, Any]:
    """Load a previously saved search index from disk."""

    return load_index(file_path)
