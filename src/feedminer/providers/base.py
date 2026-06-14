from abc import ABC, abstractmethod

from ..models import FeedItem


class BaseProvider(ABC):
    scraper: str = "http"

    @abstractmethod
    def is_active(self, url: str) -> bool:
        """Return True if this provider handles the given URL."""
        ...

    @abstractmethod
    def process(self, html: str, source_url: str) -> list[FeedItem]:
        """Parse HTML and return a list of FeedItem instances."""
        ...

    @property
    def feed_title(self) -> str:
        return self.__class__.__name__

    @property
    def feed_filename(self) -> str | None:
        """Override to set a custom output filename (without .xml extension).
        Return None to fall back to the default URL-derived name."""
        return None
