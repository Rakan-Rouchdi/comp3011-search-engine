"""Tests for the inverted index construction logic."""

import unittest

from src.indexer import build_inverted_index, get_word_entry, normalize_text, tokenize


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


if __name__ == "__main__":
    unittest.main()
