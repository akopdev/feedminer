import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://yalebooks.yale.edu"


class YaleProvider(BaseProvider):
    DOMAIN = "yalebooks.yale.edu"

    @property
    def feed_title(self) -> str:
        return "Yale University Press — New Releases"

    def is_active(self, url: str) -> bool:
        return urlparse(url).netloc.endswith(self.DOMAIN)

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        grid = soup.find("div", class_="isbn-grid")
        if not grid:
            logger.warning("No isbn-grid found on %s", source_url)
            return []

        items = []
        for card in grid.find_all("div", class_="book-wrapper"):
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
        return items

    def _card_to_item(self, card) -> FeedItem:
        title_tag = card.select_one("p.sp__the-title")
        title = title_tag.get_text(strip=True)

        link_tag = card.select_one("div.image-wrapper a")
        href = link_tag["href"]
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        # Author is an unwrapped text node inside div.book-info
        info = card.find("div", class_="book-info")
        author = None
        if info:
            raw = " ".join(
                " ".join(str(node).split())
                for node in info.children
                if isinstance(node, NavigableString) and node.strip()
            )
            author = raw or None

        image_url = None
        img = card.select_one("img.lazyload[data-src]")
        if img:
            image_url = img["data-src"].split("?")[0]

        return FeedItem(
            title=title,
            url=url,
            author=author,
            image_url=image_url,
        )
