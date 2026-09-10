"""robots.txt handling.

Uses the standard-library ``urllib.robotparser`` for allow/disallow rules and
additionally extracts ``Crawl-delay`` (which ``robotparser`` does not expose).

Behaviour when ``robots.txt`` cannot be fetched:

- HTTP 404 (or any non-200 response) means "no robots.txt" -> allow, warn-free.
- A network error is ambiguous -> we allow the request but log a clear warning,
  because most sites without a reachable robots.txt are still safe to crawl
  politely. If you prefer a *strict* policy, raise ``strict=True``.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger("compliant_scraper.robots")

_CRAWL_DELAY_RE = re.compile(r"^\s*crawl-delay\s*:\s*([0-9.]+)\s*$", re.IGNORECASE)


class RobotsCache:
    """Fetches and caches robots.txt per host, answering fetch permission."""

    def __init__(
        self,
        user_agent: str,
        timeout: float = 15.0,
        strict: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.strict = strict
        self._session = session or requests.Session()
        self._parsers: dict[str, RobotFileParser | None] = {}
        self._crawl_delays: dict[str, float | None] = {}

    def _key(self, url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        return parsed.netloc.lower(), parsed.scheme

    def _load(self, netloc: str, scheme: str) -> None:
        if netloc in self._parsers:
            return
        robots_url = f"{scheme}://{netloc}/robots.txt"
        parser: RobotFileParser | None = None
        delay: float | None = None

        try:
            resp = self._session.get(
                robots_url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            if resp.status_code == 200:
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(resp.text.splitlines())
                delay = self._extract_crawl_delay(resp.text)
            # Any other status (404, 401, ...) => treat as "no robots.txt".
        except requests.RequestException as exc:
            if self.strict:
                # Refuse to crawl when we cannot confirm the rules.
                logger.warning(
                    "could not fetch %s (%s); strict mode: treating as disallowed",
                    robots_url,
                    exc,
                )
            else:
                logger.warning(
                    "could not fetch %s (%s); proceeding with caution",
                    robots_url,
                    exc,
                )
        self._parsers[netloc] = parser
        self._crawl_delays[netloc] = delay

    @staticmethod
    def _extract_crawl_delay(robots_text: str) -> float | None:
        for line in robots_text.splitlines():
            if line.strip().startswith("#"):
                continue
            match = _CRAWL_DELAY_RE.match(line)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        return None

    def can_fetch(self, url: str) -> bool:
        """Return True if the URL is allowed by the site's robots.txt."""
        netloc, scheme = self._key(url)
        self._load(netloc, scheme)
        parser = self._parsers.get(netloc)
        if parser is None:
            # No robots.txt available: permissive (unless strict).
            return not self.strict
        return parser.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        """Return the site's Crawl-delay directive, if any."""
        netloc, scheme = self._key(url)
        self._load(netloc, scheme)
        return self._crawl_delays.get(netloc)
