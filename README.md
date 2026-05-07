# COMP3011 Coursework 2: Website Search Tool

This project is a Python command-line search tool for `https://quotes.toscrape.com/`.

It can:
- crawl the website
- build an inverted index of words in each page
- save and load the index from disk
- print the index entry for a word
- find pages containing a single word or all words in a multi-word query

## Features
- Case-insensitive indexing and search
- Inverted index stores both word frequency and word positions
- Multi-word search returns pages containing all query words
- Single-file JSON index storage
- 6-second politeness delay between crawler requests
- Unit tests for crawler, indexer, search, and CLI behavior

## Crawl Scope
The crawler is intentionally scoped to the main quote listing pages of `https://quotes.toscrape.com/`.

It crawls:
- the homepage, which represents the first quote listing page
- paginated listing pages such as `/page/2`, `/page/3`, and so on

It does not crawl:
- author pages
- tag pages
- login pages
- other non-listing internal links

The homepage and `/page/1` contain the same first listing page, so the crawler treats them as one page to avoid duplicate indexing.

## Project Structure
```text
src/
  crawler.py
  indexer.py
  search.py
  main.py
tests/
  test_crawler.py
  test_indexer.py
  test_search.py
  test_main.py
data/
  index.json
```

## Requirements
- Python 3
- `requests`
- `beautifulsoup4`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Virtual Environment
Create and activate a virtual environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How To Run
Run commands from the project root.

### Build the index
```bash
python3 -m src.main build
```

This will:
- crawl `https://quotes.toscrape.com/`
- build the inverted index
- save it to `data/index.json`

Note: this may take some time because the crawler respects a 6-second politeness window between requests.

### Load the saved index
```bash
python3 -m src.main load
```

### Print the inverted index for one word
```bash
python3 -m src.main print nonsense
```

### Find matching pages for a query
Single-word query:

```bash
python3 -m src.main find indifference
```

Multi-word query:

```bash
python3 -m src.main find good friends
```

For multi-word queries, `find` returns pages that contain all query words. The words do not need to be adjacent.

## Testing
Run all tests with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Testing Strategy
The tests are split by module so each part of the search tool can be checked separately before testing the full workflow.

- `test_crawler.py` checks URL normalization, quote-listing crawl scope, duplicate `/page/1` handling, quote-content extraction, request failures, and the 6-second politeness rule.
- `test_indexer.py` checks tokenization, lowercase indexing, word frequency, word positions, page metadata, and JSON save/load behavior.
- `test_search.py` checks single-word search, multi-word all-query-word search, case-insensitive queries, missing words, empty queries, and the phrase-search helper.
- `test_main.py` checks the command-line workflow for `build`, `load`, `print`, `find`, missing arguments, and unknown commands.

Crawler tests use mocked responses instead of making live network requests. Politeness tests use fake time and fake sleep functions, so they prove the 6-second delay logic without making the test suite wait. Persistence tests use temporary directories so they do not depend on or damage the real saved index file.

## Manual Verification
After building the index, the saved file can be checked with:

```bash
python3 -m src.main load
python3 -m src.main print good
python3 -m src.main find good friends
```

These commands verify that the saved index can be loaded, printed, and searched from the command line.

## Design Summary
- `crawler.py` fetches pages, extracts visible text, finds internal links, and respects the politeness delay.
- `indexer.py` tokenizes text, builds the inverted index, and saves/loads JSON.
- `search.py` handles single-word search, multi-word all-terms search, and a tested phrase-search helper.
- `main.py` provides the coursework CLI commands.

## Data Structure
The inverted index uses this structure:

```json
{
  "inverted_index": {
    "good": {
      "https://quotes.toscrape.com/page/1/": {
        "frequency": 2,
        "positions": [0, 2]
      }
    }
  }
}
```

This is simple to explain, easy to save as JSON, and keeps enough position information for phrase-style checks if needed.

## Error Handling
The program handles:
- missing index file when `load`, `print`, or `find` is used before `build`
- invalid JSON in the saved index file
- unknown CLI commands
- missing command arguments
- crawler request failures

## Design Rationale
- Case-insensitive indexing keeps search behaviour predictable for users.
- Word positions are stored alongside frequency so the index contains enough information for more precise search operations.
- JSON storage keeps the saved index readable and easy to inspect for a small coursework dataset.
- The crawler uses a 6-second politeness window to avoid sending rapid repeated requests to the website.
- Multi-word `find` uses the inverted index to intersect pages containing all query words, which is efficient and simple to explain.

## GenAI Statement
Generative AI tools were used as supporting tools during this coursework. ChatGPT was used mainly to interpret the brief, plan the development workflow, evaluate design decisions, and structure the explanation for the final video. Codex was used mainly for repository auditing, code review, test suggestions, and identifying small implementation risks.

This support was useful for reviewing the project from a stricter perspective. For example, the review process identified that `/` and `/page/1` could be indexed as duplicate versions of the first quote listing page, and it also highlighted a politeness edge case where a failed request still needed to count as a request attempt. These issues were then fixed and verified with focused tests.

AI suggestions were not accepted automatically. One important example was multi-word search: an exact phrase interpretation was considered, but the final implementation keeps all-query-word matching because the coursework example indicates that `find good friends` should return pages containing both `good` and `friends`. This required comparing the AI suggestion against the brief, checking the code behaviour, and justifying the final design decision.

Overall, GenAI improved development speed and supported critical review, but responsibility for understanding, testing, and validating the final implementation remained with the developer.
