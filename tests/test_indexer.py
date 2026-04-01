"""Tests for the inverted index construction logic."""

import json
import tempfile
import unittest
from pathlib import Path

from src.indexer import (
    build_inverted_index,
    get_word_entry,
    load_index,
    normalize_text,
    save_index,
    tokenize,
)


class IndexerTests(unittest.TestCase):
    def test_normalize_text_converts_text_to_lowercase(self) -> None:
        self.assertEqual(normalize_text("Good FRIENDS"), "good friends")

    def test_tokenize_removes_basic_punctuation_and_lowercases_words(self) -> None:
        text = "Good friends, good books, and a sleepy conscience."
        self.assertEqual(
            tokenize(text),
            ["good", "friends", "good", "books", "and", "a", "sleepy", "conscience"],
        )

    def test_build_inverted_index_stores_frequency_and_positions(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Page 1",
                "text": "Good friends good books",
            }
        ]

        index_data = build_inverted_index(pages)

        self.assertEqual(
            index_data["inverted_index"]["good"]["https://quotes.toscrape.com/page/1/"],
            {"frequency": 2, "positions": [0, 2]},
        )
        self.assertEqual(
            index_data["inverted_index"]["friends"]["https://quotes.toscrape.com/page/1/"],
            {"frequency": 1, "positions": [1]},
        )

    def test_build_inverted_index_is_case_insensitive(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Page 1",
                "text": "Good good GOOD",
            }
        ]

        index_data = build_inverted_index(pages)

        self.assertIn("good", index_data["inverted_index"])
        self.assertNotIn("Good", index_data["inverted_index"])
        self.assertEqual(
            index_data["inverted_index"]["good"]["https://quotes.toscrape.com/page/1/"][
                "frequency"
            ],
            3,
        )

    def test_build_inverted_index_keeps_page_metadata(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Quotes to Scrape",
                "text": "Life is good",
            }
        ]

        index_data = build_inverted_index(pages)

        self.assertEqual(
            index_data["pages"]["https://quotes.toscrape.com/page/1/"]["title"],
            "Quotes to Scrape",
        )

    def test_get_word_entry_normalizes_the_lookup_word(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Page 1",
                "text": "Indifference is costly",
            }
        ]
        index_data = build_inverted_index(pages)

        self.assertEqual(
            get_word_entry(index_data, "INDIFFERENCE"),
            {
                "https://quotes.toscrape.com/page/1/": {
                    "frequency": 1,
                    "positions": [0],
                }
            },
        )

    def test_get_word_entry_returns_empty_dict_for_missing_word(self) -> None:
        index_data = build_inverted_index([])

        self.assertEqual(get_word_entry(index_data, "missing"), {})

    def test_save_and_load_index_round_trip(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Page 1",
                "text": "Good friends good books",
            }
        ]
        index_data = build_inverted_index(pages)

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "index.json"

            save_index(index_data, file_path)
            loaded_index = load_index(file_path)

        self.assertEqual(loaded_index, index_data)

    def test_save_index_creates_parent_directories(self) -> None:
        index_data = build_inverted_index([])

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "folder" / "index.json"

            save_index(index_data, file_path)

            self.assertTrue(file_path.exists())

    def test_load_index_raises_file_not_found_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "missing.json"

            with self.assertRaises(FileNotFoundError) as context:
                load_index(file_path)

        self.assertIn("Index file not found", str(context.exception))

    def test_load_index_raises_value_error_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.json"
            file_path.write_text("{not valid json}", encoding="utf-8")

            with self.assertRaises(ValueError) as context:
                load_index(file_path)

        self.assertIn("Index file is not valid JSON", str(context.exception))

    def test_save_index_writes_readable_json(self) -> None:
        index_data = build_inverted_index([])

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "index.json"

            save_index(index_data, file_path)
            saved_data = json.loads(file_path.read_text(encoding="utf-8"))

        self.assertEqual(saved_data, index_data)


if __name__ == "__main__":
    unittest.main()
