import asyncio
from types import SimpleNamespace

import pytest
from requests import Response
from requests.exceptions import HTTPError

from feedminer.scrapers import firecrawl
from feedminer.scrapers.firecrawl import FirecrawlScraper


def http_error(status, message="boom"):
    response = Response()
    response.status_code = status
    return HTTPError(message, response=response)


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def scrape_url(self, url, formats):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(html=outcome)


@pytest.fixture
def sleeps(monkeypatch):
    waited = []

    async def fake_sleep(seconds):
        waited.append(seconds)

    monkeypatch.setattr(firecrawl.asyncio, "sleep", fake_sleep)
    return waited


def scraper(outcomes, **kwargs):
    s = FirecrawlScraper(api_key="fc-test", **kwargs)
    s._client = FakeClient(outcomes)
    return s


def test_fetch_retries_rate_limit_using_server_hint(sleeps):
    s = scraper([http_error(429, "Rate limit exceeded ... please retry after 13s"), "<html/>"])
    assert asyncio.run(s.fetch("https://example.com")) == "<html/>"
    assert sleeps == [14]


def test_fetch_uses_default_wait_without_hint(sleeps):
    s = scraper([http_error(429), "<html/>"], default_wait=7)
    assert asyncio.run(s.fetch("https://example.com")) == "<html/>"
    assert sleeps == [7]


def test_fetch_gives_up_after_retries(sleeps):
    s = scraper([http_error(429)] * 3, retries=2)
    with pytest.raises(HTTPError):
        asyncio.run(s.fetch("https://example.com"))
    assert s._client.calls == 3


def test_fetch_does_not_retry_other_errors(sleeps):
    s = scraper([http_error(500)])
    with pytest.raises(HTTPError):
        asyncio.run(s.fetch("https://example.com"))
    assert sleeps == []
