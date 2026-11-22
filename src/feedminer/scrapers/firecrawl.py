import asyncio
import logging
import re

from firecrawl.v1.client import V1FirecrawlApp
from requests.exceptions import HTTPError

from .base import BaseScraper

logger = logging.getLogger(__name__)

RETRY_AFTER_RE = re.compile(r"retry after (\d+)s")


class FirecrawlScraper(BaseScraper):
    def __init__(self, api_key: str, retries: int = 5, default_wait: int = 20):
        self._client = V1FirecrawlApp(api_key=api_key)
        self._retries = retries
        self._default_wait = default_wait

    async def fetch(self, url: str) -> str:
        # The plan is rate limited per minute and providers scrape concurrently,
        # so wait out 429s instead of failing the page.
        for attempt in range(self._retries + 1):
            try:
                result = await asyncio.to_thread(self._client.scrape_url, url, formats=["html"])
                return result.html or ""
            except HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status != 429 or attempt == self._retries:
                    raise
                match = RETRY_AFTER_RE.search(str(exc))
                wait = int(match.group(1)) + 1 if match else self._default_wait
                logger.info("Firecrawl rate limit hit for %s, retrying in %ss", url, wait)
                await asyncio.sleep(wait)
