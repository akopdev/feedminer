import asyncio
import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from ..scrapers.base import BaseScraper
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nature.com"


class NatureIssuesProvider(BaseProvider):
    """Latest issues of Nature magazine.

    The source URL is the volumes index. ``process`` picks the newest volumes and
    ``enrich`` expands each of them into its issues (a volume holds ~4 issues).
    """

    DOMAIN = "nature.com"
    PATH = "/nature/volumes"
    VOLUMES = 2

    @property
    def feed_title(self) -> str:
        return "Nature — Issues"

    @property
    def feed_filename(self) -> str:
        return "nature-issues"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(self.DOMAIN) and parsed.path.rstrip("/") == self.PATH

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        links = soup.select('a[href^="/nature/volumes/"]')
        volumes = []
        for link in links:
            if re.fullmatch(r"/nature/volumes/\d+", link["href"]) and link["href"] not in volumes:
                volumes.append(link["href"])
        if not volumes:
            logger.warning("No volumes found on %s", source_url)
            return []
        volumes.sort(key=lambda href: int(href.rsplit("/", 1)[1]), reverse=True)
        return [
            FeedItem(title=href.rsplit("/", 1)[1], url=f"{BASE_URL}{href}")
            for href in volumes[: self.VOLUMES]
        ]

    async def enrich(self, items: list[FeedItem], scraper: BaseScraper) -> list[FeedItem]:
        pages = await asyncio.gather(*(self._fetch_volume(i.url, scraper) for i in items))
        issues = [issue for page in pages for issue in page]
        return sorted(issues, key=lambda i: i.published_at or datetime.min, reverse=True)

    async def _fetch_volume(self, url: str, scraper: BaseScraper) -> list[FeedItem]:
        try:
            return self.parse_volume(await scraper.fetch(url))
        except Exception as exc:
            logger.warning("Could not fetch volume page %s: %s", url, exc)
            return []

    def parse_volume(self, html: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")
        items = []
        for card in soup.select('li[itemtype="https://schema.org/PublicationIssue"]'):
            try:
                items.append(self._card_to_item(card))
            except Exception as exc:
                logger.warning("Skipping malformed issue: %s", exc)
        return items

    def _card_to_item(self, card) -> FeedItem:
        link = card.select_one("a[href]")
        href = link["href"]
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        number = card.select_one('[itemprop="issueNumber"]')["content"]

        published_at = None
        date_tag = card.select_one('[itemprop="datePublished"]')
        if date_tag:
            try:
                published_at = datetime.strptime(date_tag["content"], "%d %B %Y")
            except (KeyError, ValueError):
                pass

        headline = None
        description = None
        blurb = card.select_one("[data-show-more]")
        if blurb:
            paragraph = blurb.find("p")
            if paragraph:
                description = " ".join(paragraph.get_text().split()) or None
                paragraph.extract()
            headline = " ".join(blurb.get_text().split()) or None

        title = f"Issue {number}: {headline}" if headline else f"Issue {number}"

        image_url = None
        img = card.select_one("img[src]")
        if img:
            image_url = re.sub(r"/w\d+/", "/w440/", img["src"], count=1)

        return FeedItem(
            title=title,
            url=url,
            description=description,
            published_at=published_at,
            image_url=image_url,
        )
