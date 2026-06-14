import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from ..models import FeedItem
from .base import BaseProvider

logger = logging.getLogger(__name__)


class ScienceMagazineProvider(BaseProvider):
    DOMAIN = "sciencemagazinedigital.org"

    @property
    def feed_title(self) -> str:
        return "Science Magazine — Issues"

    @property
    def feed_filename(self) -> str:
        return "science-magazine-issues"

    def is_active(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            parsed.netloc.endswith(self.DOMAIN)
            and "gtxapi/issuelist" in parsed.path
        )

    def process(self, html: str, source_url: str) -> list[FeedItem]:
        try:
            data = json.loads(html)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from %s: %s", source_url, exc)
            return []

        issues = data.get("groupDetails", [])
        if not issues:
            logger.warning("No issues found in response from %s", source_url)
            return []

        items = []
        for issue in issues:
            try:
                items.append(self._issue_to_item(issue))
            except Exception as exc:
                logger.warning("Skipping malformed issue: %s", exc)
        return items

    def _issue_to_item(self, issue: dict) -> FeedItem:
        title = issue["issueName"]
        url = issue["documentLink"]

        published_at = None
        if issue.get("publishDate"):
            published_at = datetime.fromtimestamp(
                issue["publishDate"] / 1000, tz=timezone.utc
            ).replace(tzinfo=None)

        image_url = issue.get("coverImage") or None
        description = issue.get("description") or None

        return FeedItem(
            title=title,
            url=url,
            description=description,
            published_at=published_at,
            image_url=image_url,
        )
