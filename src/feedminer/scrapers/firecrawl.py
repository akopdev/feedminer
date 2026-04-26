import asyncio

from firecrawl import FirecrawlApp

from .base import BaseScraper


class FirecrawlScraper(BaseScraper):
    def __init__(self, api_key: str):
        self._client = FirecrawlApp(api_key=api_key)

    async def fetch(self, url: str) -> str:
        result = await asyncio.to_thread(self._client.scrape_url, url, {"formats": ["html"]})
        return result.get("html", "")
