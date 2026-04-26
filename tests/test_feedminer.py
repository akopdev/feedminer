import pytest

from feedminer.feedminer import process_url, run
from feedminer.models import FeedItem
from feedminer.providers.base import BaseProvider
from feedminer.scrapers.base import BaseScraper


class StubScraper(BaseScraper):
    def __init__(self, html: str = "<html></html>"):
        self._html = html

    async def fetch(self, url: str) -> str:
        return self._html


class StubProvider(BaseProvider):
    def __init__(
        self, domain: str, items: list[FeedItem] | None = None, raise_on_process: bool = False
    ):
        self._domain = domain
        self._items = items or []
        self._raise = raise_on_process

    def is_active(self, url: str) -> bool:
        return self._domain in url

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        if self._raise:
            raise RuntimeError("provider exploded")
        return self._items


def scrapers(extra: dict | None = None) -> dict:
    s = {"http": StubScraper()}
    if extra:
        s.update(extra)
    return s


@pytest.mark.asyncio
async def test_process_url_no_matching_provider():
    _, feed = await process_url("https://unknown.example.com", scrapers(), [])
    assert feed is None


@pytest.mark.asyncio
async def test_process_url_provider_failure_is_isolated():
    provider = StubProvider("example.com", raise_on_process=True)
    _, feed = await process_url("https://example.com", scrapers(), [provider])
    assert feed is None


@pytest.mark.asyncio
async def test_process_url_success():
    item = FeedItem(title="My Book", url="https://example.com/book/1", author="Jane Doe")
    provider = StubProvider("example.com", items=[item])
    _, feed = await process_url("https://example.com/books", scrapers(), [provider])
    assert feed is not None
    assert len(feed.items) == 1
    assert feed.items[0].title == "My Book"


@pytest.mark.asyncio
async def test_process_url_uses_provider_scraper():
    firecrawl_scraper = StubScraper("<html>from firecrawl</html>")

    class FirecrawlProvider(StubProvider):
        scraper = "firecrawl"

    captured = []

    class CapturingScraper(BaseScraper):
        async def fetch(self, url: str) -> str:
            captured.append("firecrawl")
            return "<html></html>"

    provider = FirecrawlProvider("example.com")
    s = {"http": StubScraper(), "firecrawl": CapturingScraper()}
    await process_url("https://example.com", s, [provider])
    assert captured == ["firecrawl"]


@pytest.mark.asyncio
async def test_process_url_falls_back_when_scraper_missing():
    class FirecrawlProvider(StubProvider):
        scraper = "firecrawl"

    provider = FirecrawlProvider("example.com")
    # Only http available — should fall back without raising
    _, feed = await process_url("https://example.com", scrapers(), [provider])
    assert feed is not None


@pytest.mark.asyncio
async def test_run_writes_xml_file(tmp_path):
    item = FeedItem(title="A Title", url="https://example.com/page")
    provider = StubProvider("example.com", items=[item])
    await run(["https://example.com"], scrapers(), [provider], tmp_path)
    out = tmp_path / "example-com.xml"
    assert out.exists()
    content = out.read_text()
    assert "<rss" in content
    assert "A Title" in content


@pytest.mark.asyncio
async def test_run_skips_failed_urls(tmp_path):
    provider = StubProvider("example.com", raise_on_process=True)
    await run(["https://example.com"], scrapers(), [provider], tmp_path)
    assert not any(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_run_concurrent(tmp_path):
    items_a = [FeedItem(title="Book A", url="https://a.com/1")]
    items_b = [FeedItem(title="Book B", url="https://b.com/1")]
    providers = [
        StubProvider("a.com", items=items_a),
        StubProvider("b.com", items=items_b),
    ]
    await run(["https://a.com", "https://b.com"], scrapers(), providers, tmp_path)
    assert (tmp_path / "a-com.xml").exists()
    assert (tmp_path / "b-com.xml").exists()
