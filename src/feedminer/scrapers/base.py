from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> str:
        """Fetch the URL and return raw HTML content."""
        ...
