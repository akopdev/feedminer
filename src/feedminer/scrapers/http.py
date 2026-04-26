import aiohttp

from .base import BaseScraper

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; feedminer/0.1; +https://github.com/akopdev/feedminer)"
}


class AsyncHttpScraper(BaseScraper):
    def __init__(self, timeout: int = 30):
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch(self, url: str) -> str:
        async with aiohttp.ClientSession(timeout=self._timeout, headers=_DEFAULT_HEADERS) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
