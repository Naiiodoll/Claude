"""Configuration loading and validation.

Configuration is written as TOML (read with the standard-library ``tomllib``,
so no extra dependency is required). See ``config.example.toml`` for a complete,
commented example.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a configuration file is missing or invalid."""


@dataclass
class FieldSpec:
    """How to extract a single field from an item element."""

    name: str
    selector: str
    attribute: str = "text"  # "text" or the name of an HTML attribute
    multiple: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldSpec":
        if "name" not in data or "selector" not in data:
            raise ConfigError("each field needs 'name' and 'selector'")
        return cls(
            name=str(data["name"]),
            selector=str(data["selector"]),
            attribute=str(data.get("attribute", "text")),
            multiple=bool(data.get("multiple", False)),
        )


@dataclass
class PaginationSpec:
    """How to follow pagination / "next page" links."""

    selector: str | None = None  # CSS selector for the "next" link
    attribute: str = "href"
    max_pages: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PaginationSpec":
        if not data:
            return cls()
        return cls(
            selector=data.get("selector"),
            attribute=str(data.get("attribute", "href")),
            max_pages=int(data.get("max_pages", 1)),
        )


@dataclass
class ItemSpec:
    """How to find item elements on a page and extract fields from each."""

    selector: str
    fields: list[FieldSpec]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemSpec":
        if "selector" not in data:
            raise ConfigError("'item.selector' is required")
        raw_fields = data.get("fields", [])
        if not raw_fields:
            raise ConfigError("'item.fields' must contain at least one field")
        return cls(
            selector=str(data["selector"]),
            fields=[FieldSpec.from_dict(f) for f in raw_fields],
        )


@dataclass
class Config:
    """Top-level scraper configuration."""

    name: str
    user_agent: str
    start_urls: list[str]
    item: ItemSpec
    pagination: PaginationSpec = field(default_factory=PaginationSpec)
    delay: float = 2.0  # seconds between requests to the same host
    timeout: float = 15.0
    max_retries: int = 3
    backoff_base: float = 1.0  # base seconds for exponential backoff
    allowed_domains: list[str] | None = None  # optional allow-list of hosts

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        user_agent = data.get("user_agent")
        if not user_agent:
            raise ConfigError(
                "'user_agent' is required and should include contact "
                "information, e.g. 'MyBot/1.0 (+https://example.com/bot)'"
            )
        if "start_urls" not in data or not data["start_urls"]:
            raise ConfigError("'start_urls' must contain at least one URL")
        if "item" not in data:
            raise ConfigError("'item' section is required")

        return cls(
            name=str(data.get("name", "unnamed-scraper")),
            user_agent=str(user_agent),
            start_urls=[str(u) for u in data["start_urls"]],
            item=ItemSpec.from_dict(data["item"]),
            pagination=PaginationSpec.from_dict(data.get("pagination")),
            delay=float(data.get("delay", 2.0)),
            timeout=float(data.get("timeout", 15.0)),
            max_retries=int(data.get("max_retries", 3)),
            backoff_base=float(data.get("backoff_base", 1.0)),
            allowed_domains=(
                [str(d) for d in data["allowed_domains"]]
                if data.get("allowed_domains")
                else None
            ),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        return cls.from_dict(data)


def load_config(path: str | Path) -> Config:
    """Load and validate a scraper configuration from a TOML file."""
    return Config.from_file(path)
