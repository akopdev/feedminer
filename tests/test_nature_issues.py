import asyncio
from datetime import datetime

from feedminer.providers.nature_issues import NatureIssuesProvider

PROVIDER = NatureIssuesProvider()
SOURCE = "https://www.nature.com/nature/volumes"

VOLUMES_HTML = """
<html><body><ul>
  <li><time datetime="2026-10">October 2026</time><a href="/nature/volumes/658">Volume 658</a></li>
  <li><time datetime="2026-11">November 2026</time><a href="/nature/volumes/659">Volume 659</a></li>
  <li><a href="/nature/volumes/659">Volume 659</a></li>
  <li><a href="/nature/volumes/657">Volume 657</a></li>
  <li><a href="/nature/volumes/659/issues/8141">not a volume</a></li>
</ul></body></html>
"""


def volume_html(issues):
    cards = "".join(
        f"""
        <li class="flex-box" itemscope="itemscope" itemtype="https://schema.org/PublicationIssue" itemprop="hasPart">
          <div data-component="equal-height-item">
            <a itemprop="url" href=/nature/volumes/{vol}/issues/{num}>
              <img src="https://media.springernature.com/w200/springer-static/cover-hires/journal/41586/{vol}/{num}" alt="">
              <h2 itemprop="issueNumber" content="{num}">No. {num}
                <span itemprop="datePublished" content="{date}">{date}</span></h2>
            </a>
            <div class="pa20" data-show-more data-show-more-length="200">
              {headline}
              <p>{blurb}</p>
            </div>
          </div>
        </li>"""
        for vol, num, date, headline, blurb in issues
    )
    return f'<html><body><ul id="issue-list">{cards}</ul></body></html>'


VOLUME_659 = volume_html(
    [
        ("659", "8141", "19 November 2026", "Stepping stones", "Stone shaped dispersal."),
        ("659", "8140", "12 November 2026", "", ""),
    ]
)
VOLUME_658 = volume_html([("658", "8137", "29 October 2026", "Deep time", "Old rocks.")])


class FakeScraper:
    async def fetch(self, url):
        if url.endswith("/659"):
            return VOLUME_659
        if url.endswith("/658"):
            return VOLUME_658
        raise RuntimeError("boom")


def test_is_active():
    assert PROVIDER.is_active(SOURCE)
    assert PROVIDER.is_active(SOURCE + "/")
    assert not PROVIDER.is_active("https://www.nature.com/nature/volumes/659")
    assert not PROVIDER.is_active("https://www.nature.com/books-culture")
    assert not PROVIDER.is_active("https://example.com/nature/volumes")


def test_process_picks_newest_volumes():
    items = PROVIDER.process(VOLUMES_HTML, SOURCE)
    assert [i.url for i in items] == [
        "https://www.nature.com/nature/volumes/659",
        "https://www.nature.com/nature/volumes/658",
    ]


def test_process_empty():
    assert PROVIDER.process("<html></html>", SOURCE) == []


def test_parse_volume_fields():
    first, second = PROVIDER.parse_volume(VOLUME_659)
    assert first.title == "Issue 8141: Stepping stones"
    assert first.url == "https://www.nature.com/nature/volumes/659/issues/8141"
    assert first.description == "Stone shaped dispersal."
    assert first.published_at == datetime(2026, 11, 19)
    assert first.image_url == (
        "https://media.springernature.com/w440/springer-static/cover-hires/journal/41586/659/8141"
    )
    assert second.title == "Issue 8140"
    assert second.description is None


def test_enrich_expands_volumes_into_issues_newest_first():
    volumes = PROVIDER.process(VOLUMES_HTML, SOURCE)
    issues = asyncio.run(PROVIDER.enrich(volumes, FakeScraper()))
    assert [i.title.split(":")[0] for i in issues] == ["Issue 8141", "Issue 8140", "Issue 8137"]


def test_enrich_tolerates_failed_volume():
    volumes = PROVIDER.process(VOLUMES_HTML.replace("658", "600"), SOURCE)
    issues = asyncio.run(PROVIDER.enrich(volumes, FakeScraper()))
    assert len(issues) == 2


def test_process_accepts_absolute_volume_links():
    html = VOLUMES_HTML.replace('href="/nature', 'href="https://www.nature.com/nature')
    items = PROVIDER.process(html, SOURCE)
    assert [i.url for i in items] == [
        "https://www.nature.com/nature/volumes/659",
        "https://www.nature.com/nature/volumes/658",
    ]
