import json
import logging
import re
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://press.princeton.edu"
ALGOLIA_QUERY_URL = "https://{app_id}-dsn.algolia.net/1/indexes/books_search/query"
PLACEHOLDER_IMG = "placeholder/book.jpg"


class PrincetonProvider(BaseProvider):
    DOMAIN = "press.princeton.edu"

    @property
    def feed_title(self) -> str:
        return "Princeton University Press — New Books"

    def is_active(self, url: str) -> bool:
        return urlparse(url).netloc.endswith(self.DOMAIN)

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        app_id, api_key = self._extract_credentials(html)
        if not app_id or not api_key:
            logger.error("Could not find Algolia credentials on %s", source_url)
            return []

        # urllib.request is synchronous; acceptable for a prototype with a small URL list
        hits = self._query_algolia(app_id, api_key)
        hits.sort(key=lambda h: h.get("book_published_date_us", 0), reverse=True)

        items = []
        for hit in hits:
            try:
                items.append(self._hit_to_item(hit))
            except Exception as exc:
                logger.warning("Skipping malformed hit %s: %s", hit.get("book_title"), exc)
        return items

    def _extract_credentials(self, html: str) -> tuple[str, str]:
        app_id = re.search(r'"appId"\s*:\s*"([^"]+)"', html)
        api_key = re.search(r'"apiKey"\s*:\s*"([^"]+)"', html)
        return (app_id.group(1) if app_id else ""), (api_key.group(1) if api_key else "")

    def _query_algolia(self, app_id: str, api_key: str, hits_per_page: int = 20) -> list[dict]:
        payload = json.dumps(
            {
                "query": "",
                "hitsPerPage": hits_per_page,
                "attributesToRetrieve": [
                    "book_title",
                    "book_isbn",
                    "contrib_full_name",
                    "book_published_date_us",
                    "book_overview",
                    "book_listing",
                ],
                "filters": "book_primary_edition:true",
            }
        ).encode()
        req = urllib.request.Request(
            ALGOLIA_QUERY_URL.format(app_id=app_id),
            data=payload,
            headers={
                "X-Algolia-Application-Id": app_id,
                "X-Algolia-API-Key": api_key,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("hits", [])

    def _hit_to_item(self, hit: dict) -> FeedItem:
        title = hit["book_title"]
        isbn = str(hit["book_isbn"])

        authors = hit.get("contrib_full_name", [])
        author = ", ".join(authors) if authors else None

        pub_ts = hit.get("book_published_date_us")
        published_at = datetime.fromtimestamp(pub_ts, tz=timezone.utc) if pub_ts else None

        description = None
        if overview := hit.get("book_overview"):
            description = BeautifulSoup(overview, "lxml").get_text(separator=" ", strip=True)

        image_url = None
        if listing_html := hit.get("book_listing"):
            img = BeautifulSoup(listing_html, "lxml").find("img")
            if img and img.get("src") and PLACEHOLDER_IMG not in img["src"]:
                image_url = img["src"].split("?")[0]

        return FeedItem(
            title=title,
            url=f"{BASE_URL}/isbn/{isbn}",
            author=author,
            published_at=published_at,
            description=description,
            image_url=image_url,
        )
