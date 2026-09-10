import pytest

from scraper.config import FieldSpec, ItemSpec
from scraper.parser import extract_records, find_next_url

HTML = """
<div class="quote">
  <span class="text">Life is what happens.</span>
  <small class="author">John Lennon</small>
  <a class="tag" href="/tag/life">life</a>
  <a class="tag" href="/tag/hope">hope</a>
</div>
<div class="quote">
  <span class="text">Stay hungry.</span>
  <small class="author">Steve Jobs</small>
</div>
"""


def test_extract_records_basic_fields():
    item = ItemSpec(
        selector="div.quote",
        fields=[
            FieldSpec(name="text", selector="span.text"),
            FieldSpec(name="author", selector="small.author"),
        ],
    )
    records = extract_records(HTML, item)
    assert len(records) == 2
    assert records[0]["text"] == "Life is what happens."
    assert records[0]["author"] == "John Lennon"
    assert records[1]["author"] == "Steve Jobs"


def test_extract_records_multiple():
    item = ItemSpec(
        selector="div.quote",
        fields=[FieldSpec(name="tags", selector="a.tag", multiple=True)],
    )
    records = extract_records(HTML, item)
    assert records[0]["tags"] == ["life", "hope"]
    assert records[1]["tags"] == []


def test_extract_missing_field_is_none():
    item = ItemSpec(
        selector="div.quote",
        fields=[FieldSpec(name="tags", selector="a.tag")],
    )
    records = extract_records(HTML, item)
    assert records[1]["tags"] is None


def test_find_next_url_resolves_relative():
    html = '<a class="next" href="/page/2/">Next</a>'
    assert find_next_url(html, "a.next", "href", "https://example.com/") == (
        "https://example.com/page/2/"
    )


def test_find_next_url_missing_returns_none():
    assert find_next_url(HTML, "a.next", "href", "https://example.com/") is None
