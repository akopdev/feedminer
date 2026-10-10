import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)


class ORBooksProvider(BaseProvider):
    DOMAIN = "orbooks.com"

    @property
    def feed_title(self) -> str:
        return "OR Books — Catalog"

    @property
    def feed_filename(self) -> str:
        return "or-books-catalog"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(self.DOMAIN) and parsed.path.startswith("/catalog")

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        grid = soup.find("ul", class_="productGrid")
        if not grid:
            logger.warning("No productGrid found on %s", source_url)
            return []

        items = []
        for card in grid.select("li.product article.card"):
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
        return items

    def _card_to_item(self, card) -> FeedItem:
        link = card.select_one("a.card-title-name")
        title = link.get_text(strip=True)
        url = link["href"]

        subtitle_tag = card.select_one("div.card-category-name")
        description = subtitle_tag.get_text(strip=True) if subtitle_tag else None

        author_tag = card.select_one("div.card-text a")
        author = author_tag.get_text(strip=True) if author_tag else None

        image_url = None
        img = card.select_one("img.card-image")
        if img:
            srcset = img.get("data-srcset", "")
            # Pick the 640w rendition when available, else fall back to src.
            for part in srcset.split(","):
                if part.strip().endswith(" 640w"):
                    image_url = part.strip().split()[0]
            image_url = image_url or img.get("src")

        return FeedItem(
            title=title,
            url=url,
            description=description or None,
            author=author,
            image_url=image_url,
        )
