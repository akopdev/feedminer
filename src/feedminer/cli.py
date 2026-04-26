import argparse
import asyncio
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from . import __version__
from .feedminer import run
from .providers.hup_harvard import HUPHarvardProvider
from .providers.mit_press import MITProvider
from .providers.princeton import PrincetonProvider
from .providers.stanford import StanfordProvider
from .providers.yale import YaleProvider
from .scrapers.firecrawl import FirecrawlScraper
from .scrapers.http import AsyncHttpScraper
from .settings import Settings


def main():
    parser = argparse.ArgumentParser(
        prog="feedminer",
        description="Fetch URLs and produce RSS feeds.",
        argument_default=argparse.SUPPRESS,
    )
    parser.add_argument("urls_file", type=Path, help="Text file with one URL per line")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=Path("feeds"),
        metavar="DIR",
        help="Directory to write RSS feed files into (default: feeds/)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    args = parser.parse_args()

    try:
        settings = Settings(**vars(args))
    except ValidationError as e:
        error = e.errors(include_url=False, include_context=False)[0]
        sys.exit("Error ({}): {}".format(error.get("loc", ("system",))[0], error.get("msg")))

    logging.basicConfig(
        level=logging.DEBUG if settings.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not settings.urls_file.exists():
        sys.exit(f"File not found: {settings.urls_file}")

    urls = [
        line.strip()
        for line in settings.urls_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if not urls:
        sys.exit(f"No URLs found in {settings.urls_file}")

    scrapers = {"http": AsyncHttpScraper()}
    if settings.firecrawl_key:
        scrapers["firecrawl"] = FirecrawlScraper(api_key=settings.firecrawl_key)

    providers = [HUPHarvardProvider(), PrincetonProvider(), MITProvider(), YaleProvider(), StanfordProvider()]

    asyncio.run(run(urls, scrapers, providers, settings.output_dir))


if __name__ == "__main__":
    main()
