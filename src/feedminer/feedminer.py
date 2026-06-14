import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

from .models import Feed
from .providers.base import BaseProvider
from .scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


def _find_provider(url: str, providers: list[BaseProvider]) -> BaseProvider | None:
    for provider in providers:
        if provider.is_active(url):
            return provider
    return None


def _url_to_filename(url: str) -> str:
    netloc = urlparse(url).netloc or url
    netloc = netloc.removeprefix("www.")
    return netloc.replace(".", "-") + ".xml"


async def process_url(
    url: str,
    scrapers: dict[str, BaseScraper],
    providers: list[BaseProvider],
) -> tuple[str, Feed | None]:
    provider = _find_provider(url, providers)
    if provider is None:
        logger.warning("No provider matched for %s — skipping", url)
        return url, None, None

    scraper = scrapers.get(provider.scraper)
    if scraper is None:
        logger.warning(
            "%s requires the '%s' scraper which is not configured — falling back to http",
            provider.__class__.__name__,
            provider.scraper,
        )
        scraper = scrapers.get("http")

    if scraper is None:
        logger.error("No scraper available for %s", url)
        return url, None, None

    try:
        logger.info("Fetching %s (scraper: %s)", url, provider.scraper)
        html = await scraper.fetch(url)
        items = provider.process(html, url)
        logger.info("Parsed %d items from %s", len(items), url)
        filename = provider.feed_filename or _url_to_filename(url).removesuffix(".xml")
        feed = Feed(title=provider.feed_title, url=url, items=items)
        return url, feed, filename
    except Exception as exc:
        logger.error("Failed to process %s: %s", url, exc)
        return url, None, None


async def run(
    urls: list[str],
    scrapers: dict[str, BaseScraper],
    providers: list[BaseProvider],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = [process_url(url, scrapers, providers) for url in urls]
    results = await asyncio.gather(*tasks)

    for url, feed, filename in results:
        if feed is None:
            continue
        xml = feed.to_rss()
        out_path = output_dir / (filename + ".xml")
        out_path.write_text(xml, encoding="utf-8")
        logger.info("Saved %s (%d items)", out_path, len(feed.items))

    success = sum(1 for _, f, _fn in results if f is not None)
    print(f"Done: {success}/{len(urls)} feeds written to {output_dir}/")
