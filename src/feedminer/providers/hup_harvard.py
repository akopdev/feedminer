import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.hup.harvard.edu"


class HUPHarvardProvider(BaseProvider):
    DOMAIN = "hup.harvard.edu"

    @property
    def feed_title(self) -> str:
        return "Harvard University Press — New Releases"

    def is_active(self, url: str) -> bool:
        return urlparse(url).netloc.endswith(self.DOMAIN)

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        items = []

        cards = soup.find_all("article", attrs={"data-component": "cards:book-card"})
        logger.debug("Found %d book cards on %s", len(cards), source_url)

        for card in cards:
            try:
                title_tag = card.find("h2", attrs={"itemprop": "name"})
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                link_tag = card.find("a", attrs={"itemtype": "url"})
                if not link_tag or not link_tag.get("href"):
                    continue
                href = link_tag["href"]
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

                author_tag = card.find("span", attrs={"itemprop": "author"})
                author = author_tag.get_text(strip=True) if author_tag else None

                image_url = None
                img_tag = card.find("img", class_="cover-img")
                if img_tag:
                    image_url = img_tag.get("data-src") or img_tag.get("src")

                items.append(
                    FeedItem(
                        title=title,
                        url=url,
                        author=author,
                        image_url=image_url,
                    )
                )
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
                continue

        return items
