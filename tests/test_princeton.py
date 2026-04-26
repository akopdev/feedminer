import json
from unittest.mock import MagicMock, patch

from feedminer.providers.princeton import PrincetonProvider

PROVIDER = PrincetonProvider()

SAMPLE_HTML = """
<html><head></head><body>
<div data-app-id="TESTAPPID" data-api-key="TESTAPIKEY">
<script>{"appId":"TESTAPPID","apiKey":"TESTAPIKEY"}</script>
</div>
</body></html>
"""

ALGOLIA_HITS = [
    {
        "book_title": "The Art of Thinking",
        "book_isbn": 9780691234567,
        "contrib_full_name": ["Jane Smith", "John Doe"],
        "book_published_date_us": 1745000000,
        "book_overview": "<p>A deep dive into <b>cognitive science</b>.</p>",
        "book_listing": (
            '<span><img loading="lazy"'
            ' src="https://pup-assets.imgix.net/onix/images/9780691234567.jpg?w=230&auto=format"'
            ' alt="The Art of Thinking"></span>'
        ),
    },
    {
        "book_title": "No Cover Book",
        "book_isbn": 9780691999999,
        "contrib_full_name": ["Alice"],
        "book_published_date_us": 1744000000,
        "book_overview": "",
        "book_listing": (
            '<span><img loading="lazy"'
            ' src="https://pup-assets.imgix.net/onix/placeholder/book.jpg?w=230&auto=format"'
            ' alt="No Cover"></span>'
        ),
    },
]


def _mock_urlopen(hits=ALGOLIA_HITS):
    payload = json.dumps({"hits": hits, "nbHits": len(hits)}).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=payload)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_is_active_matches_princeton():
    assert PROVIDER.is_active("https://press.princeton.edu/books")
    assert PROVIDER.is_active("https://press.princeton.edu/isbn/9780691234567")


def test_is_active_rejects_others():
    assert not PROVIDER.is_active("https://princeton.edu")
    assert not PROVIDER.is_active("https://example.com")


def test_extract_credentials():
    app_id, api_key = PROVIDER._extract_credentials(SAMPLE_HTML)
    assert app_id == "TESTAPPID"
    assert api_key == "TESTAPIKEY"


def test_extract_credentials_missing():
    app_id, api_key = PROVIDER._extract_credentials("<html></html>")
    assert app_id == ""
    assert api_key == ""


def test_process_returns_items():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen()):
        items = PROVIDER.process(SAMPLE_HTML, "https://press.princeton.edu/books")
    assert len(items) == 2


def test_process_correct_fields():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen()):
        items = PROVIDER.process(SAMPLE_HTML, "https://press.princeton.edu/books")
    first = items[0]
    assert first.title == "The Art of Thinking"
    assert first.url == "https://press.princeton.edu/isbn/9780691234567"
    assert first.author == "Jane Smith, John Doe"
    assert first.description == "A deep dive into cognitive science ."
    assert first.image_url == "https://pup-assets.imgix.net/onix/images/9780691234567.jpg"
    assert first.published_at is not None


def test_process_placeholder_image_excluded():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen()):
        items = PROVIDER.process(SAMPLE_HTML, "https://press.princeton.edu/books")
    assert items[1].image_url is None


def test_process_sorted_by_date_descending():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen()):
        items = PROVIDER.process(SAMPLE_HTML, "https://press.princeton.edu/books")
    assert items[0].published_at > items[1].published_at


def test_process_missing_credentials_returns_empty():
    items = PROVIDER.process("<html></html>", "https://press.princeton.edu/books")
    assert items == []
