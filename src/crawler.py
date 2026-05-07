"""Website crawling utilities for the coursework search tool."""

from __future__ import annotations

import re
import time
from collections import deque
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


DEFAULT_BASE_URL = "https://quotes.toscrape.com/"
DEFAULT_TIMEOUT = 10
DEFAULT_POLITENESS_DELAY = 6.0
LISTING_PAGE_PATTERN = r"^/page/\d+$"


def normalize_url(url: str) -> str:
    """Normalize a URL so duplicate links are easier to detect."""

    parsed_url = urlparse(url)
    path = parsed_url.path or "/"

    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc.lower(),
            path,
            "",
            parsed_url.query,
            "",
        )
    )


def canonical_listing_url(url: str, base_url: str) -> str:
    """Return the canonical URL for a quote listing page.

    The homepage and /page/1 show the same quote listing content, so the
    crawler stores them as one page to avoid duplicate indexing.
    """

    normalized_url = normalize_url(url)
    parsed_url = urlparse(normalized_url)

    if parsed_url.path == "/page/1":
        return normalize_url(base_url)

    return normalized_url


def is_internal_url(url: str, base_url: str) -> bool:
    """Return True when a URL belongs to the target website."""

    parsed_url = urlparse(url)
    parsed_base_url = urlparse(base_url)
    return parsed_url.netloc == parsed_base_url.netloc


def is_listing_page_url(url: str, base_url: str) -> bool:
    """Return True for the homepage and paginated quote listing pages only."""

    if not is_internal_url(url, base_url):
        return False

    path = urlparse(url).path or "/"
    return path == "/" or bool(re.match(LISTING_PAGE_PATTERN, path))


def extract_text(soup: BeautifulSoup) -> str:
    """Extract visible quote listing text from a page."""

    for tag in soup(["script", "style"]):
        tag.decompose()

    quote_blocks = soup.select(".quote")
    if quote_blocks:
        text_parts = [
            quote_block.get_text(separator=" ", strip=True)
            for quote_block in quote_blocks
        ]
        text = " ".join(text_parts)
    else:
        text = soup.get_text(separator=" ", strip=True)

    return " ".join(text.split())


def extract_links(soup: BeautifulSoup, current_url: str, base_url: str) -> list[str]:
    """Return normalized quote-listing links discovered on a page."""

    current_listing_url = canonical_listing_url(current_url, base_url)
    internal_links: list[str] = []
    seen_links: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        absolute_url = urljoin(current_url, anchor["href"])
        normalized_url = canonical_listing_url(absolute_url, base_url)

        if not is_listing_page_url(normalized_url, base_url):
            continue

        if normalized_url == current_listing_url:
            continue

        if normalized_url in seen_links:
            continue

        seen_links.add(normalized_url)
        internal_links.append(normalized_url)

    return internal_links


def parse_page(html: str, url: str, base_url: str) -> dict[str, Any]:
    """Parse one HTML page into crawl data."""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    return {
        "url": canonical_listing_url(url, base_url),
        "title": title,
        "text": extract_text(soup),
        "links": extract_links(soup, url, base_url),
    }


def fetch_page(
    session: requests.Session,
    url: str,
    *,
    politeness_delay: float = DEFAULT_POLITENESS_DELAY,
    last_request_time: float | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    sleep_func: Any = time.sleep,
    time_func: Any = time.monotonic,
) -> tuple[str, float]:
    """Fetch one page while respecting the politeness window."""

    current_time = time_func()
    if last_request_time is not None:
        elapsed = current_time - last_request_time
        if elapsed < politeness_delay:
            sleep_func(politeness_delay - elapsed)

    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text, time_func()


def crawl_site(
    base_url: str = DEFAULT_BASE_URL,
    *,
    politeness_delay: float = DEFAULT_POLITENESS_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
    sleep_func: Any = time.sleep,
    time_func: Any = time.monotonic,
) -> list[dict[str, Any]]:
    """Crawl internal pages from the target site using breadth-first search."""

    active_session = session or requests.Session()
    normalized_base_url = canonical_listing_url(base_url, base_url)
    queue = deque([normalized_base_url])
    visited: set[str] = set()
    crawled_pages: list[dict[str, Any]] = []
    last_request_time: float | None = None

    while queue:
        current_url = queue.popleft()
        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            html, last_request_time = fetch_page(
                active_session,
                current_url,
                politeness_delay=politeness_delay,
                last_request_time=last_request_time,
                timeout=timeout,
                sleep_func=sleep_func,
                time_func=time_func,
            )
        except requests.RequestException:
            last_request_time = time_func()
            continue

        page_data = parse_page(html, current_url, normalized_base_url)
        crawled_pages.append(page_data)

        for link in page_data["links"]:
            if link not in visited:
                queue.append(link)

    return crawled_pages
