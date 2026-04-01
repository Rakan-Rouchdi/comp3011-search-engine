"""Workflow helpers and CLI for the coursework search index."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from src.crawler import DEFAULT_BASE_URL, crawl_site
from src.indexer import build_inverted_index, get_word_entry, load_index, save_index
from src.search import find_query


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


def format_word_entry(word: str, entry: dict[str, Any]) -> str:
    """Create printable output for one word's posting list."""

    if not entry:
        return f"No index entry found for '{word}'."

    lines = [f"Inverted index for '{word}':"]
    for url in sorted(entry):
        page_entry = entry[url]
        lines.append(
            f"- {url} | frequency={page_entry['frequency']} | "
            f"positions={page_entry['positions']}"
        )
    return "\n".join(lines)


def format_search_results(query: str, results: list[str]) -> str:
    """Create printable output for search results."""

    if not results:
        return f"No pages found for query '{query}'."

    lines = [f"Pages matching '{query}':"]
    for url in results:
        lines.append(f"- {url}")
    return "\n".join(lines)


def run_cli(
    args: list[str],
    *,
    index_path: str | Path = DEFAULT_INDEX_PATH,
) -> tuple[int, str]:
    """Run the coursework CLI and return an exit code with output text."""

    if not args:
        return 1, "Usage: build | load | print <word> | find <query>"

    command = args[0]

    if command == "build":
        index_data = build_search_index(output_path=index_path)
        page_count = len(index_data["pages"])
        word_count = len(index_data["inverted_index"])
        return (
            0,
            f"Index built successfully with {page_count} pages and {word_count} words.",
        )

    if command == "load":
        index_data = load_saved_index(index_path)
        page_count = len(index_data["pages"])
        word_count = len(index_data["inverted_index"])
        return (
            0,
            f"Index loaded successfully with {page_count} pages and {word_count} words.",
        )

    if command == "print":
        if len(args) < 2:
            return 1, "Usage: print <word>"

        word = args[1]
        index_data = load_saved_index(index_path)
        word_entry = get_word_entry(index_data, word)
        return 0, format_word_entry(word, word_entry)

    if command == "find":
        if len(args) < 2:
            return 1, "Usage: find <query>"

        query = " ".join(args[1:])
        index_data = load_saved_index(index_path)
        results = find_query(index_data, query)
        return 0, format_search_results(query, results)

    return 1, f"Unknown command: {command}"


def main() -> int:
    """Entry point for running the CLI as a script."""

    try:
        exit_code, output = run_cli(sys.argv[1:])
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 1

    print(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
