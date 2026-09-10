"""HTTP fetching with politeness built in.

Responsibilities:

- check ``robots.txt`` before every request,
- throttle requests per-host (using the larger of the configured ``delay`` and
  the site's ``Crawl-delay``),
- retry transient failures (network errors, 429, 5xx) with exponential backoff
  plus jitter, honouring ``Retry-After`` when present.
"""

from __future__ import annotations

import logging
import random
import time
from urllib.parse import urlparse

import requests

from .config import Config
from .robots import RobotsCache

logger = logging.getLogger("compliant_scraper.fetcher")

_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


class Fetcher:
    """A polite HTTP client that wraps :class:`requests.Session`."""

    def __init__(self, config: Config, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
        self.robots = RobotsCache(
            config.user_agent,
            timeout=config.timeout,
            session=self.session,
        )
        self._last_request: dict[str, float] = {}

    def _delay_for(self, url: str) -> float:
        """Effective delay: max(config delay, site Crawl-delay)."""
        site_delay = self.robots.crawl_delay(url)
        if site_delay is not None:
            return max(self.config.delay, site_delay)
        return self.config.delay

    def _throttle(self, url: str) -> None:
        netloc = urlparse(url).netloc.lower()
        delay = self._delay_for(url)
        last = self._last_request.get(netloc)
        if last is not None:
            wait = delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request[netloc] = time.monotonic()

    @staticmethod
    def _backoff(attempt: int, base: float) -> float:
        """Exponential backoff with jitter, capped at 60s."""
        return min(base * (2**attempt), 60.0) + random.uniform(0, base)

    def _retry_after(self, response: requests.Response) -> float | None:
        header = response.headers.get("Retry-After")
        if header is None:
            return None
        try:
            return float(header)
        except ValueError:
            # Retry-After may be an HTTP-date; fall back to exponential backoff.
            return None

    def can_fetch(self, url: str) -> bool:
        return self.robots.can_fetch(url)

    def get(self, url: str) -> requests.Response | None:
        """Fetch ``url`` politely, returning the response or ``None`` if skipped.

        Returns ``None`` when the URL is disallowed by robots.txt, the host is
        outside ``allowed_domains``, or all retries are exhausted.
        """
        netloc = urlparse(url).netloc.lower()

        if self.config.allowed_domains and netloc not in {
            d.lower() for d in self.config.allowed_domains
        }:
            logger.warning("skipping %s: host not in allowed_domains", url)
            return None

        if not self.robots.can_fetch(url):
            logger.info("skipping %s: disallowed by robots.txt", url)
            return None

        for attempt in range(self.config.max_retries + 1):
            self._throttle(url)
            try:
                response = self.session.get(url, timeout=self.config.timeout)
            except requests.RequestException as exc:
                if attempt < self.config.max_retries:
                    wait = self._backoff(attempt, self.config.backoff_base)
                    logger.warning(
                        "request to %s failed (%s); retrying in %.1fs",
                        url,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                logger.error("request to %s failed permanently: %s", url, exc)
                return None

            if response.status_code in _RETRYABLE_STATUS and attempt < self.config.max_retries:
                wait = self._retry_after(response) or self._backoff(
                    attempt, self.config.backoff_base
                )
                logger.warning(
                    "got %d from %s; retrying in %.1fs",
                    response.status_code,
                    url,
                    wait,
                )
                time.sleep(wait)
                continue

            if response.status_code == 200:
                return response

            logger.warning("got unexpected status %d from %s; skipping", response.status_code, url)
            return None

        return None
