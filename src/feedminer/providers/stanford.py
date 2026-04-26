import logging
import re
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.sup.org"


class StanfordProvider(BaseProvider):
    DOMAIN = "sup.org"

    @property
    def feed_title(self) -> str:
        return "Stanford University Press — Middle East Studies"

    def is_active(self, url: str) -> bool:
        return urlparse(url).netloc.endswith(self.DOMAIN)

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")

        # Cards are <li> elements that contain a book link
        seen = set()
        cards = []
        for link in soup.find_all("a", href=re.compile(r"^/books/")):
            li = link.find_parent("li")
            if li and id(li) not in seen:
                seen.add(id(li))
                cards.append(li)

        if not cards:
            logger.warning("No book cards found on %s", source_url)
            return []

        items = []
        for card in cards:
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
        return items

    def _card_to_item(self, card) -> FeedItem:
        link = card.find("a", href=re.compile(r"^/books/"))
        title = link.get_text(strip=True)
        url = f"{BASE_URL}{link['href']}"

        # Next.js image proxy — decode the real cover URL from the `url` query param
        image_url = None
        img = card.find("img", class_="object-cover")
        if img and img.get("src"):
            qs = parse_qs(urlparse(img["src"]).query)
            raw = qs.get("url", [None])[0]
            if raw:
                image_url = unquote(raw)

        # Two sibling divs with text-press-sand-dark: subtitle then author
        sand_divs = card.find_all("div", class_=re.compile(r"text-press-sand-dark"))
        description = sand_divs[0].get_text(strip=True) if len(sand_divs) > 0 else None
        author = sand_divs[1].get_text(strip=True) if len(sand_divs) > 1 else None

        return FeedItem(
            title=title,
            url=url,
            author=author,
            description=description,
            image_url=image_url,
        )
