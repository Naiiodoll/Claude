"""Export scraped records to JSON or CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    """Make otherwise-serialisable values JSON-safe."""
    if value is None:
        return None
    return value


def export_json(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2, default=_json_default)


def export_csv(records: list[dict[str, Any]], path: Path) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(k for record in records for k in record))
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Flatten list values (e.g. tags) into a "|"-joined string.
            row = {
                key: "|".join(value) if isinstance(value, list) else value
                for key, value in record.items()
            }
            writer.writerow(row)


def export(records: list[dict[str, Any]], path: Path, fmt: str) -> None:
    fmt = fmt.lower()
    if fmt == "json":
        export_json(records, path)
    elif fmt == "csv":
        export_csv(records, path)
    else:
        raise ValueError(f"unsupported export format: {fmt!r} (use 'json' or 'csv')")
