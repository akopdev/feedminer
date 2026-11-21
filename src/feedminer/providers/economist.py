import logging
import re
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.economist.com"
DATE_RE = re.compile(r"^\s*([A-Z][a-z]+) (\d{1,2})(?:st|nd|rd|th) (\d{4})\s*$")


class EconomistWeeklyEditionProvider(BaseProvider):
    """The current weekly edition as a single item: cover + table of contents."""

    DOMAIN = "economist.com"
    PATH = "/weeklyedition"
    scraper = "firecrawl"

    @property
    def feed_title(self) -> str:
        return "The Economist — Weekly Edition"

    @property
    def feed_filename(self) -> str:
        return "economist-weekly-edition"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.endswith(self.DOMAIN) and parsed.path.rstrip("/") == self.PATH

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        soup = BeautifulSoup(html, "lxml")

        sections = self._sections(soup)
        if not sections:
            logger.warning("No articles found on %s", source_url)
            return []

        published_at = self._edition_date(soup)
        url = source_url
        if published_at:
            url = f"{BASE_URL}{self.PATH}/{published_at:%Y-%m-%d}"

        title = "Weekly edition"
        if published_at:
            title += f", {published_at:%B} {published_at.day}, {published_at.year}"
        headline_tag = soup.select_one("h1.en-cover-headline")
        if headline_tag:
            title += f": {headline_tag.get_text(strip=True)}"

        cover = soup.select_one('img[src*="_DE_"]') or soup.select_one("main img[src]")
        image_url = cover["src"] if cover else None

        parts = []
        if image_url:
            parts.append(f'<p><img src="{escape(image_url)}" alt="Cover"/></p>')
        for section, articles in sections:
            parts.append(f"<h3>{escape(section)}</h3><ul>")
            parts.extend(
                f'<li><a href="{escape(href)}">{escape(text)}</a></li>' for text, href in articles
            )
            parts.append("</ul>")

        return [
            FeedItem(
                title=title,
                url=url,
                description="".join(parts),
                published_at=published_at,
                image_url=image_url,
            )
        ]

    def _sections(self, soup) -> list[tuple[str, list[tuple[str, str]]]]:
        # Section headers and article teasers are siblings in document order, so walk
        # both together and attach each teaser to the most recent header.
        sections = []
        for tag in soup.select('h2[class*="section-header__title"], h3[class*="teaser__headline"]'):
            if tag.name == "h2":
                sections.append((tag.get_text(strip=True), []))
                continue
            link = tag.select_one("a[href]")
            if not link:
                continue
            if not sections:
                sections.append(("", []))
            href = link["href"]
            href = href if href.startswith("http") else f"{BASE_URL}{href}"
            sections[-1][1].append((link.get_text(strip=True), href))
        return [(name, articles) for name, articles in sections if articles]

    def _edition_date(self, soup) -> datetime | None:
        for text in soup.find_all(string=DATE_RE):
            month, day, year = DATE_RE.match(text.strip()).groups()
            try:
                return datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
            except ValueError:
                continue
        return None
