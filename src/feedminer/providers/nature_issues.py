import logging
import re
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nature.com"
HEADING_RE = re.compile(r"Volume (\d+) Issue (\d+), (\d{1,2} [A-Z][a-z]+ \d{4})")


class NatureIssuesProvider(BaseProvider):
    """The current issue of Nature as a single item: cover + table of contents."""

    DOMAIN = "nature.com"
    scraper = "firecrawl"
    PATH = "/nature/current-issue"

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

        heading = soup.find("h1", string=HEADING_RE)
        if not heading:
            logger.warning("No issue heading found on %s", source_url)
            return []
        volume, number, date = HEADING_RE.search(heading.get_text()).groups()
        published_at = datetime.strptime(date, "%d %B %Y")

        cover = soup.select_one(".app-volumes-cover img[src]")
        image_url = cover["src"] if cover else None

        headline = None
        blurb = None
        copy = soup.select_one(".app-volumes-cover__copy")
        if copy:
            headline_tag = copy.select_one("h2")
            headline = _text(headline_tag) if headline_tag else None
            # The blurb is cut into a visible paragraph and a hidden "show more" remainder.
            pieces = copy.select("p[data-promo-text], .app-promo-text__hidden-container")
            blurb = " ".join("".join(piece.get_text() for piece in pieces).split()) or None

        parts = []
        if image_url:
            parts.append(f'<p><img src="{escape(image_url)}" alt="Cover"/></p>')
        if blurb:
            parts.append(f"<p>{escape(blurb)}</p>")
        for section, articles in self._sections(soup):
            parts.append(f"<h3>{escape(section)}</h3><ul>")
            parts.extend(
                f'<li><a href="{escape(href)}">{escape(text)}</a></li>' for text, href in articles
            )
            parts.append("</ul>")

        return [
            FeedItem(
                title=f"Issue {number}: {headline}" if headline else f"Issue {number}",
                url=f"{BASE_URL}/nature/volumes/{volume}/issues/{number}",
                description="".join(parts) or None,
                published_at=published_at,
                image_url=image_url,
            )
        ]

    def _sections(self, soup) -> list[tuple[str, list[tuple[str, str]]]]:
        # Section headings and article cards come in document order, so walk both
        # together and attach each article to the most recent heading.
        sections = []
        for tag in soup.select("h3.c-section-heading, h3.c-card__title"):
            if "c-section-heading" in tag.get("class", []):
                sections.append((_text(tag), []))
                continue
            link = tag.select_one("a[href]")
            if not link:
                continue
            if not sections:
                sections.append(("", []))
            href = link["href"]
            href = href if href.startswith("http") else f"{BASE_URL}{href}"
            sections[-1][1].append((_text(link), href))
        return [(name, articles) for name, articles in sections if articles]


def _text(tag) -> str:
    # get_text(strip=True) would glue words around inline tags like <i>.
    return " ".join(tag.get_text().split())
