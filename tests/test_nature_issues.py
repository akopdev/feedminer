from datetime import datetime

from feedminer.providers.nature_issues import NatureIssuesProvider

PROVIDER = NatureIssuesProvider()
SOURCE = "https://www.nature.com/nature/current-issue"
COVER = "https://media.springernature.com/w440/springer-static/cover-hires/journal/41586/659/8141"

SAMPLE_HTML = f"""
<html><body>
  <h1 class="u-h2 u-mb-0 u-mr-8">Volume 659 Issue 8141, 19 November 2026</h1>
  <div class="app-volumes-cover" data-test="issue-cover-container">
    <div class="app-volumes-cover__copy" data-test="issue-description"><div>
      <h2 class="u-h3">Stepping stones</h2>
      <p data-promo-text=""><span>Climate is a factor. But </span><a href="https://doi.org/x">Jeffrey Rose</a><span> and colleagues reveal stone. Signs at</span></p>
      <div class="app-promo-text__hidden-container u-js-hide"><span> palaeolakes were absent.</span></div>
      <span>Show more</span>
    </div></div>
    <div class="app-volumes-cover__image"><img src="{COVER}" alt="Cover"></div>
  </div>
  <h2>This Week</h2>
  <h3 class="c-section-heading c-section-heading--no-bt">Editorial</h3>
  <article><h3 class="c-card__title">
    <a href="https://www.nature.com/articles/d41586-026-03707-7">Open up peer review</a>
  </h3></article>
  <h3 class="c-section-heading c-section-heading--no-bt">Empty</h3>
  <h3 class="c-section-heading c-section-heading--no-bt">News &amp; Views</h3>
  <article><h3 class="c-card__title">
    <a href="/articles/d41586-026-03273-y">Intra-stellar: a <i>star</i> inside a giant star</a>
  </h3></article>
  <article><h3 class="c-card__title">No link here</h3></article>
</body></html>
"""


def test_is_active():
    assert PROVIDER.is_active(SOURCE)
    assert PROVIDER.is_active(SOURCE + "/")
    assert not PROVIDER.is_active("https://www.nature.com/nature/volumes")
    assert not PROVIDER.is_active("https://www.nature.com/books-culture")
    assert not PROVIDER.is_active("https://example.com/nature/current-issue")


def test_process_single_issue_item():
    [item] = PROVIDER.process(SAMPLE_HTML, SOURCE)
    assert item.title == "Issue 8141: Stepping stones"
    assert item.url == "https://www.nature.com/nature/volumes/659/issues/8141"
    assert item.published_at == datetime(2026, 11, 19)
    assert item.image_url == COVER


def test_process_description_has_cover_blurb_and_contents():
    [item] = PROVIDER.process(SAMPLE_HTML, SOURCE)
    desc = item.description
    assert desc.startswith(f'<p><img src="{COVER}"')
    assert (
        "<p>Climate is a factor. But Jeffrey Rose and colleagues reveal stone. "
        "Signs at palaeolakes were absent.</p>"
    ) in desc
    assert "Show more" not in desc
    assert "<h3>News &amp; Views</h3>" in desc
    assert (
        '<li><a href="https://www.nature.com/articles/d41586-026-03707-7">'
        "Open up peer review</a></li>"
    ) in desc
    assert (
        '<a href="https://www.nature.com/articles/d41586-026-03273-y">'
        "Intra-stellar: a star inside a giant star</a>"
    ) in desc
    assert desc.index("Editorial") < desc.index("News &amp; Views")
    assert "Empty" not in desc


def test_process_without_heading_returns_empty():
    assert PROVIDER.process("<html><body><h1>Nature</h1></body></html>", SOURCE) == []
