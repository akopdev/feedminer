import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime

from pydantic import BaseModel


class FeedItem(BaseModel):
    title: str
    url: str
    description: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    image_url: str | None = None


class Feed(BaseModel):
    title: str
    url: str
    description: str = ""
    items: list[FeedItem] = []
    generated_at: datetime = None

    def model_post_init(self, __context) -> None:
        if self.generated_at is None:
            object.__setattr__(self, "generated_at", datetime.now(tz=timezone.utc))

    def to_rss(self) -> str:
        rss = ET.Element(
            "rss", version="2.0", attrib={"xmlns:media": "http://search.yahoo.com/mrss/"}
        )
        channel = ET.SubElement(rss, "channel")

        ET.SubElement(channel, "title").text = self.title
        ET.SubElement(channel, "link").text = self.url
        ET.SubElement(channel, "description").text = self.description or self.title
        ET.SubElement(channel, "lastBuildDate").text = format_datetime(self.generated_at)

        for item in self.items:
            el = ET.SubElement(channel, "item")
            ET.SubElement(el, "title").text = item.title
            ET.SubElement(el, "link").text = item.url
            ET.SubElement(el, "guid", isPermaLink="true").text = item.url
            if item.description:
                ET.SubElement(el, "description").text = item.description
            if item.author:
                ET.SubElement(el, "author").text = item.author
            if item.published_at:
                ET.SubElement(el, "pubDate").text = format_datetime(item.published_at)
            if item.image_url:
                ET.SubElement(el, "media:content", url=item.image_url, medium="image")

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")
