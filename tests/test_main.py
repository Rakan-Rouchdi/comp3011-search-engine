"""Tests for the command-line workflow helpers."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.indexer import build_inverted_index, save_index
from src.main import run_cli


class MainTests(unittest.TestCase):
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
        ]
        self.index_data = build_inverted_index(self.pages)

    def test_run_cli_requires_a_command(self) -> None:
        exit_code, output = run_cli([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Usage:", output)

    def test_run_cli_build_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.json"

            with patch("src.main.build_search_index", return_value=self.index_data) as mock_build:
                exit_code, output = run_cli(["build"], index_path=index_path)

        mock_build.assert_called_once_with(output_path=index_path)
        self.assertEqual(exit_code, 0)
        self.assertIn("Index built successfully", output)

    def test_run_cli_load_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.json"
            save_index(self.index_data, index_path)

            exit_code, output = run_cli(["load"], index_path=index_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Index loaded successfully", output)

    def test_run_cli_print_requires_a_word(self) -> None:
        exit_code, output = run_cli(["print"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "Usage: print <word>")

    def test_run_cli_print_shows_word_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.json"
            save_index(self.index_data, index_path)

            exit_code, output = run_cli(["print", "good"], index_path=index_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Inverted index for 'good':", output)
        self.assertIn("frequency=2", output)

    def test_run_cli_find_requires_a_query(self) -> None:
        exit_code, output = run_cli(["find"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "Usage: find <query>")

    def test_run_cli_find_shows_matching_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.json"
            save_index(self.index_data, index_path)

            exit_code, output = run_cli(["find", "good", "friends"], index_path=index_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("Pages matching 'good friends':", output)
        self.assertIn("https://quotes.toscrape.com/page/1/", output)

    def test_run_cli_reports_unknown_commands(self) -> None:
        exit_code, output = run_cli(["unknown"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "Unknown command: unknown")

    def test_run_cli_propagates_missing_index_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "missing.json"

            with self.assertRaises(FileNotFoundError):
                run_cli(["load"], index_path=index_path)


if __name__ == "__main__":
    unittest.main()
