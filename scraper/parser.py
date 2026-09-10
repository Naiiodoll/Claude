"""HTML parsing and field extraction using BeautifulSoup."""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .config import FieldSpec, ItemSpec


def _extract_field(element: Any, spec: FieldSpec) -> Any:
    nodes = element.select(spec.selector)

    if spec.multiple:
        if spec.attribute == "text":
            return [n.get_text(strip=True) for n in nodes]
        # HTML attribute extraction (e.g. "href", "src", "title").
        return [n.get(spec.attribute) for n in nodes]

    node = nodes[0] if nodes else None
    if node is None:
        return None

    if spec.attribute == "text":
        return node.get_text(strip=True)
    return node.get(spec.attribute)


def extract_records(html: str, item: ItemSpec) -> list[dict[str, Any]]:
    """Parse ``html`` and return one dict per matching item element."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []
    for element in soup.select(item.selector):
        records.append(
            {spec.name: _extract_field(element, spec) for spec in item.fields}
        )
    return records


def find_next_url(html: str, selector: str | None, attribute: str, base_url: str) -> str | None:
    """Return the absolute URL of the 'next page' link, or ``None``."""
    if not selector:
        return None
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one(selector)
    if node is None:
        return None
    href = node.get(attribute)
    if not href:
        return None

    from urllib.parse import urljoin

    return urljoin(base_url, href)
