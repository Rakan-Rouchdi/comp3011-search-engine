"""Tests for the search logic built on top of the inverted index."""

import unittest

from src.indexer import build_inverted_index
from src.search import find_query, normalize_query, search_phrase, search_word


class SearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = [
            {
                "url": "https://quotes.toscrape.com/page/1/",
                "title": "Page 1",
                "text": "Good friends good books",
            },
            {
                "url": "https://quotes.toscrape.com/page/2/",
                "title": "Page 2",
                "text": "Good books make good company",
            },
            {
                "url": "https://quotes.toscrape.com/page/3/",
                "title": "Page 3",
                "text": "Friends are important and good",
            },
        ]
        self.index_data = build_inverted_index(self.pages)

    def test_normalize_query_returns_lowercase_tokens(self) -> None:
        self.assertEqual(normalize_query(" Good FRIENDS "), ["good", "friends"])

    def test_search_word_returns_all_matching_pages(self) -> None:
        self.assertEqual(
            search_word(self.index_data, "good"),
            [
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/page/2/",
                "https://quotes.toscrape.com/page/3/",
            ],
        )

    def test_search_word_is_case_insensitive(self) -> None:
        self.assertEqual(
            search_word(self.index_data, "GOOD"),
            search_word(self.index_data, "good"),
        )

    def test_search_word_returns_empty_list_for_missing_word(self) -> None:
        self.assertEqual(search_word(self.index_data, "missing"), [])

    def test_search_phrase_returns_pages_with_exact_phrase(self) -> None:
        self.assertEqual(
            search_phrase(self.index_data, "good books"),
            [
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/page/2/",
            ],
        )

    def test_search_phrase_returns_empty_list_when_words_are_not_adjacent(self) -> None:
        self.assertEqual(search_phrase(self.index_data, "good company good"), [])

    def test_search_phrase_is_case_insensitive(self) -> None:
        self.assertEqual(
            search_phrase(self.index_data, "GOOD BOOKS"),
            search_phrase(self.index_data, "good books"),
        )

    def test_find_query_handles_single_word_queries(self) -> None:
        self.assertEqual(
            find_query(self.index_data, "friends"),
            [
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/page/3/",
            ],
        )

    def test_find_query_handles_multi_word_queries(self) -> None:
        self.assertEqual(
            find_query(self.index_data, "good books"),
            [
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/page/2/",
            ],
        )

    def test_find_query_returns_empty_list_for_empty_query(self) -> None:
        self.assertEqual(find_query(self.index_data, "   "), [])


if __name__ == "__main__":
    unittest.main()
