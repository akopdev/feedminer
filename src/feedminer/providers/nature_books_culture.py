import logging
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nature.com"


class NatureBooksCultureProvider(BaseProvider):
    DOMAIN = "nature.com"
    PATH = "/books-culture"

    @property
    def feed_title(self) -> str:
        return "Nature — Books & Culture"

    @property
    def feed_filename(self) -> str:
        return "nature-com-books-culture"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(self.DOMAIN) and parsed.path.rstrip("/") == self.PATH.rstrip("/")

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.find_all("div", class_="c-article-item__wrapper")
        if not cards:
            logger.warning("No article cards found on %s", source_url)
            return []

        items = []
        for card in cards:
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
        return items

    def _card_to_item(self, card) -> FeedItem:
        title_tag = card.select_one("h3.c-article-item__title")
        title = title_tag.get_text(strip=True)

        link_tag = card.select_one("a[href]")
        href = link_tag["href"]
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        desc_tag = card.select_one(".c-article-item__standfirst p")
        description = desc_tag.get_text(strip=True) if desc_tag else None

        published_at = None
        date_tag = card.select_one(".c-article-item__date")
        if date_tag:
            try:
                published_at = datetime.strptime(date_tag.get_text(strip=True), "%d %b %Y")
            except ValueError:
                pass

        image_url = None
        img = card.select_one("img.c-article-item__image")
        if img and img.get("src"):
            src = img["src"]
            image_url = src if src.startswith("http") else f"https:{src}"

        return FeedItem(
            title=title,
            url=url,
            description=description,
            published_at=published_at,
            image_url=image_url,
        )
