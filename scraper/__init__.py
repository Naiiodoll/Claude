"""compliant-scraper: a polite, configurable web scraper.

The scraper is designed to be a *good citizen* on the web:

- honours ``robots.txt`` (both allow/disallow rules and ``Crawl-delay``),
- throttles requests per-domain,
- retries transient failures with exponential backoff + jitter,
- identifies itself with a clear, honest ``User-Agent``,
- respects ``Retry-After`` on 429 / 503 responses.

See the README for legal-usage guidance before pointing it at any site.
"""

from .config import Config, FieldSpec, PaginationSpec, load_config
from .pipeline import run

__all__ = ["Config", "FieldSpec", "PaginationSpec", "load_config", "run"]
__version__ = "0.1.0"
