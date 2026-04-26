from abc import ABC, abstractmethod

from ..models import FeedItem


class BaseProvider(ABC):
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
