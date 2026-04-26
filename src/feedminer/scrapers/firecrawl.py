import asyncio

from .base import BaseScraper


class FirecrawlScraper(BaseScraper):
    def __init__(self, api_key: str):
        try:
            from firecrawl import FirecrawlApp
        except ImportError:
            raise ImportError(
                "firecrawl-py is required for FirecrawlScraper. "
                "Install it with: pip install feedminer[firecrawl]"
            )
        self._client = FirecrawlApp(api_key=api_key)

    async def fetch(self, url: str) -> str:
        result = await asyncio.to_thread(
            self._client.scrape_url, url, {"formats": ["html"]}
        )
        return result.get("html", "")
