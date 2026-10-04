import asyncio
import logging
from html import escape
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from ..scrapers.base import BaseScraper
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.newyorker.com"


class NewYorkerDailyCartoonProvider(BaseProvider):
    DOMAIN = "newyorker.com"
    PATH = "/cartoons/daily-cartoon"

    @property
    def feed_title(self) -> str:
        return "The New Yorker — Daily Cartoon"

    @property
    def feed_filename(self) -> str:
        return "newyorker-daily-cartoon"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(self.DOMAIN) and parsed.path.rstrip("/") == self.PATH

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("div.summary-item")
        items = []
        for card in cards:
            if not card.select_one("a.summary-item__hed-link"):
                continue
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed card: %s", exc)
        if not items:
            logger.warning("No cartoons found on %s", source_url)
        return items

    def _card_to_item(self, card) -> FeedItem:
        link = card.select_one("a.summary-item__hed-link")
        title = link.get_text(strip=True)
        href = link["href"]
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        published_at = None
        time_tag = card.select_one("time")
        if time_tag:
            try:
                published_at = datetime.strptime(time_tag.get_text(strip=True), "%B %d, %Y")
            except ValueError:
                pass

        image_url = None
        img = card.select_one("img")
        if img and img.get("src"):
            image_url = img["src"]

        return FeedItem(
            title=title,
            url=url,
            published_at=published_at,
            image_url=image_url,
        )

    async def enrich(self, items: list[FeedItem], scraper: BaseScraper) -> list[FeedItem]:
        return list(await asyncio.gather(*(self._enrich_item(i, scraper) for i in items)))

    async def _enrich_item(self, item: FeedItem, scraper: BaseScraper) -> FeedItem:
        try:
            html = await scraper.fetch(item.url)
            return self._merge_detail(item, html)
        except Exception as exc:
            logger.warning("Could not fetch cartoon page %s: %s", item.url, exc)
            return item

    def _merge_detail(self, item: FeedItem, html: str) -> FeedItem:
        soup = BeautifulSoup(html, "lxml")

        caption_tag = soup.select_one(".responsive-cartoon__caption .caption__text")
        credit_tag = soup.select_one(".responsive-cartoon__credit .caption__credit")
        img = soup.select_one(".responsive-cartoon img[alt]") or soup.select_one(".responsive-cartoon img")
        summary_tag = soup.select_one('meta[name="description"]')

        caption = caption_tag.get_text(strip=True) if caption_tag else None
        credit = credit_tag.get_text(strip=True) if credit_tag else None
        alt = img.get("alt", "").strip() if img else ""
        summary = summary_tag.get("content", "").strip() if summary_tag else ""

        parts = []
        if caption:
            parts.append(f"<p><b>{escape(caption)}</b></p>")
        if alt:
            parts.append(f"<p><i>{escape(alt)}</i></p>")
        if summary:
            parts.append(f"<p>{escape(summary)}</p>")
        if credit:
            parts.append(f"<p>{escape(credit)}</p>")

        update = {}
        if parts:
            update["description"] = "".join(parts)
        if credit:
            update["author"] = credit.removeprefix("Cartoon by ").strip()
        if img and img.get("src"):
            update["image_url"] = img["src"]
        return item.model_copy(update=update)
