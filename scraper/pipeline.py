"""End-to-end scraping pipeline: fetch -> parse -> collect -> return."""

from __future__ import annotations

import logging
from typing import Any

from .config import Config
from .fetcher import Fetcher
from .parser import extract_records, find_next_url

logger = logging.getLogger("compliant_scraper.pipeline")


def run(config: Config) -> list[dict[str, Any]]:
    """Run the scraper for ``config`` and return the collected records."""
    fetcher = Fetcher(config)
    records: list[dict[str, Any]] = []

    for start_url in config.start_urls:
        url: str | None = start_url
        page = 0
        while url is not None and page < config.pagination.max_pages:
            logger.info("fetching page %d: %s", page + 1, url)
            response = fetcher.get(url)
            if response is None:
                break

            page_records = extract_records(response.text, config.item)
            logger.info("extracted %d record(s) from %s", len(page_records), url)
            records.extend(page_records)

            url = find_next_url(
                response.text,
                config.pagination.selector,
                config.pagination.attribute,
                url,
            )
            page += 1

    return records
