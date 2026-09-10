"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .exporter import export
from .pipeline import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliant-scraper",
        description="A polite, robots.txt-respecting web scraper.",
    )
    parser.add_argument(
        "config",
        help="path to a TOML config file (see config.example.toml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output/data.json",
        help="output file path (default: output/data.json)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv"],
        default="json",
        help="output format (default: json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate config and check robots.txt, without scraping",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        from .fetcher import Fetcher

        fetcher = Fetcher(config)
        for url in config.start_urls:
            status = "allowed" if fetcher.can_fetch(url) else "DISALLOWED"
            print(f"{url} -> {status}")
        print("config validated OK (dry run, nothing scraped).")
        return 0

    records = run(config)
    output = Path(args.output)
    export(records, output, args.format)
    print(f"done: scraped {len(records)} record(s) -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
