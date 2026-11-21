import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://mitpress.mit.edu"
COVER_HOST = "mit-press-new-us.imgix.net"
ISBN_RE = re.compile(r"/(97[89]\d{10})/")


class MITProvider(BaseProvider):
    DOMAIN = "mitpress.mit.edu"
    scraper = "firecrawl"

    @property
    def feed_title(self) -> str:
        return "MIT Press — New Releases"

    def is_active(self, url: str) -> bool:
        return urlparse(url).netloc.endswith(self.DOMAIN)

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        if "Access Denied" in html:
            logger.error("MIT Press blocked the request (Akamai bot protection). ")
            return []

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
        title_tag = card.select_one("p.sp__the-title a")
        title = title_tag.get_text(strip=True)

        href = title_tag["href"]
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        author_tag = card.select_one("p.sp__the-author")
        author = author_tag.get_text(strip=True) if author_tag else None

        published_at = None
        date_tag = card.select_one("p.sp__the-publication-date")
        if date_tag:
            try:
                published_at = datetime.strptime(date_tag.get_text(strip=True), "%B %d, %Y")
            except ValueError:
                pass

        return FeedItem(
            title=title,
            url=url,
            author=author,
            published_at=published_at,
            image_url=self._cover_url(card, href),
        )

    def _cover_url(self, card, href: str) -> str | None:
        # Firecrawl renders JS, so lazysizes may already have swapped data-src into src
        # and renamed the "lazyload" class; accept either form, skip the placeholder.
        for img in card.select("picture img, .image-wrapper img"):
            for attr in ("data-src", "src"):
                src = img.get(attr, "")
                if COVER_HOST in src:
                    return src.split("?")[0]

        match = ISBN_RE.search(href)
        if match:
            return f"https://{COVER_HOST}/covers/{match.group(1)}.jpg"
        return None
