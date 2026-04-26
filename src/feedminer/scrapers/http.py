import aiohttp

from .base import BaseScraper

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


class AsyncHttpScraper(BaseScraper):
    def __init__(self, timeout: int = 30):
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch(self, url: str) -> str:
        async with aiohttp.ClientSession(
            timeout=self._timeout, headers=_DEFAULT_HEADERS
        ) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
