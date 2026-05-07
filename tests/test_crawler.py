"""Tests for crawler behavior."""

import tempfile
import unittest
from unittest.mock import Mock
from pathlib import Path

import requests

from src.main import build_search_index, load_saved_index
from src.crawler import (
    canonical_listing_url,
    crawl_site,
    extract_links,
    fetch_page,
    is_listing_page_url,
    normalize_url,
    parse_page,
)


class CrawlerTests(unittest.TestCase):
    def test_normalize_url_removes_fragment_and_trailing_slash(self) -> None:
        self.assertEqual(
            normalize_url("https://quotes.toscrape.com/page/1/#top"),
            "https://quotes.toscrape.com/page/1",
        )

    def test_canonical_listing_url_treats_homepage_and_page_one_as_same_page(
        self,
    ) -> None:
        self.assertEqual(
            canonical_listing_url(
                "https://quotes.toscrape.com/page/1/",
                "https://quotes.toscrape.com/",
            ),
            "https://quotes.toscrape.com/",
        )

    def test_extract_links_returns_unique_internal_links_only(self) -> None:
        html = """
        <html>
          <body>
            <a href="/page/1/">Page 1</a>
            <a href="/page/1/">Page 1 Duplicate</a>
            <a href="https://quotes.toscrape.com/page/2/">Page 2</a>
            <a href="https://quotes.toscrape.com/author/Albert-Einstein">Author</a>
            <a href="https://example.com/page/3/">External</a>
          </body>
        </html>
        """

        page_data = parse_page(
            html,
            "https://quotes.toscrape.com/",
            "https://quotes.toscrape.com/",
        )

        self.assertEqual(
            page_data["links"],
            [
                "https://quotes.toscrape.com/page/2",
            ],
        )

    def test_is_listing_page_url_accepts_only_home_and_paginated_quote_pages(self) -> None:
        base_url = "https://quotes.toscrape.com/"

        self.assertTrue(is_listing_page_url("https://quotes.toscrape.com/", base_url))
        self.assertTrue(
            is_listing_page_url("https://quotes.toscrape.com/page/3", base_url)
        )
        self.assertFalse(
            is_listing_page_url(
                "https://quotes.toscrape.com/author/Albert-Einstein", base_url
            )
        )
        self.assertFalse(
            is_listing_page_url("https://quotes.toscrape.com/tag/life", base_url)
        )

    def test_parse_page_extracts_title_text_and_links(self) -> None:
        html = """
        <html>
          <head><title>Quotes to Scrape</title></head>
          <body>
            <div class="quote">Good friends, good books.</div>
            <a href="/page/2/">Next</a>
          </body>
        </html>
        """

        page_data = parse_page(
            html,
            "https://quotes.toscrape.com/",
            "https://quotes.toscrape.com/",
        )

        self.assertEqual(page_data["title"], "Quotes to Scrape")
        self.assertIn("Good friends, good books.", page_data["text"])
        self.assertEqual(page_data["links"], ["https://quotes.toscrape.com/page/2"])

    def test_parse_page_indexes_quote_content_not_page_navigation(self) -> None:
        html = """
        <html>
          <head><title>Quotes to Scrape</title></head>
          <body>
            <a href="/login">Login</a>
            <div class="quote">
              <span class="text">The world as we have created it.</span>
              <small class="author">Albert Einstein</small>
              <a class="tag" href="/tag/world/">world</a>
            </div>
            <li class="next"><a href="/page/2/">Next</a></li>
          </body>
        </html>
        """

        page_data = parse_page(
            html,
            "https://quotes.toscrape.com/",
            "https://quotes.toscrape.com/",
        )

        self.assertIn("The world as we have created it.", page_data["text"])
        self.assertIn("Albert Einstein", page_data["text"])
        self.assertNotIn("Login", page_data["text"])
        self.assertNotIn("Next", page_data["text"])

    def test_fetch_page_waits_for_politeness_window(self) -> None:
        session = Mock()
        session.get.return_value = Mock(text="<html></html>")
        session.get.return_value.raise_for_status = Mock()
        sleep_calls: list[float] = []

        html, last_request_time = fetch_page(
            session,
            "https://quotes.toscrape.com/",
            politeness_delay=6.0,
            last_request_time=10.0,
            sleep_func=sleep_calls.append,
            time_func=Mock(side_effect=[13.0, 16.0]),
        )

        self.assertEqual(html, "<html></html>")
        self.assertEqual(last_request_time, 16.0)
        self.assertEqual(sleep_calls, [3.0])

    def test_crawl_site_skips_duplicate_page_one_and_continues_after_failure(
        self,
    ) -> None:
        session = Mock()

        homepage_response = Mock()
        homepage_response.text = """
        <html>
          <head><title>Home</title></head>
          <body>
            <p>Welcome home</p>
            <a href="/page/1/">Page 1</a>
            <a href="/page/1/">Page 1 duplicate</a>
            <a href="/page/2/">Page 2</a>
          </body>
        </html>
        """
        homepage_response.raise_for_status = Mock()

        page_two_response = Mock()
        page_two_response.text = """
        <html>
          <head><title>Page 2</title></head>
          <body><p>Second quote page</p></body>
        </html>
        """
        page_two_response.raise_for_status = Mock()

        def get_side_effect(url: str, timeout: int) -> Mock:
            if url == "https://quotes.toscrape.com/":
                return homepage_response
            if url == "https://quotes.toscrape.com/page/2":
                return page_two_response
            raise requests.RequestException("Page failed to load")

        session.get.side_effect = get_side_effect

        pages = crawl_site(
            "https://quotes.toscrape.com/",
            politeness_delay=0.0,
            session=session,
        )

        self.assertEqual(
            [page["url"] for page in pages],
            [
                "https://quotes.toscrape.com/",
                "https://quotes.toscrape.com/page/2",
            ],
        )
        self.assertEqual(session.get.call_count, 2)

    def test_crawl_site_waits_after_failed_request_before_next_request(self) -> None:
        session = Mock()

        homepage_response = Mock()
        homepage_response.text = """
        <html>
          <head><title>Home</title></head>
          <body>
            <a href="/page/2/">Page 2</a>
            <a href="/page/3/">Page 3</a>
          </body>
        </html>
        """
        homepage_response.raise_for_status = Mock()

        page_three_response = Mock()
        page_three_response.text = """
        <html>
          <head><title>Page 3</title></head>
          <body><p>Third quote page</p></body>
        </html>
        """
        page_three_response.raise_for_status = Mock()

        def get_side_effect(url: str, timeout: int) -> Mock:
            if url == "https://quotes.toscrape.com/":
                return homepage_response
            if url == "https://quotes.toscrape.com/page/2":
                raise requests.RequestException("Page failed to load")
            if url == "https://quotes.toscrape.com/page/3":
                return page_three_response
            raise AssertionError(f"Unexpected URL: {url}")

        session.get.side_effect = get_side_effect
        sleep_calls: list[float] = []

        pages = crawl_site(
            "https://quotes.toscrape.com/",
            politeness_delay=6.0,
            session=session,
            sleep_func=sleep_calls.append,
            time_func=Mock(side_effect=[0.0, 1.0, 3.0, 4.0, 7.0, 10.0]),
        )

        self.assertEqual(
            [page["url"] for page in pages],
            [
                "https://quotes.toscrape.com/",
                "https://quotes.toscrape.com/page/3",
            ],
        )
        self.assertEqual(sleep_calls, [4.0, 3.0])

    def test_extract_links_helper_handles_relative_urls(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<a href="/page/3/">Page 3</a><a href="#local">Local</a>',
            "html.parser",
        )

        links = extract_links(
            soup,
            "https://quotes.toscrape.com/page/1",
            "https://quotes.toscrape.com/",
        )

        self.assertEqual(
            links,
            [
                "https://quotes.toscrape.com/page/3",
            ],
        )

    def test_build_search_index_crawls_builds_and_saves_index(self) -> None:
        pages = [
            {
                "url": "https://quotes.toscrape.com/",
                "title": "Home",
                "text": "Good friends good books",
                "links": [],
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "index.json"

            index_data = build_search_index(
                base_url="https://quotes.toscrape.com/",
                output_path=output_path,
                crawl_func=Mock(return_value=pages),
            )

            loaded_index = load_saved_index(output_path)

        self.assertEqual(index_data, loaded_index)
        self.assertEqual(index_data["base_url"], "https://quotes.toscrape.com/")
        self.assertIn("good", index_data["inverted_index"])


if __name__ == "__main__":
    unittest.main()
