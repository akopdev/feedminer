from datetime import datetime

from feedminer.providers.economist import EconomistWeeklyEditionProvider

PROVIDER = EconomistWeeklyEditionProvider()
SOURCE = "https://www.economist.com/weeklyedition"
COVER = (
    "https://www.economist.com/cdn-cgi/image/width=1424,quality=80,format=auto"
    "/content-assets/images/20261121_DE_US.jpg"
)

SAMPLE_HTML = f"""
<html><body><main>
  <div><p>November 21st 2026</p>
    <h1 class="text_mb-text__wleiI en-cover-headline">Axis of malice</h1>
    <figure><img alt="" src="{COVER}"></figure>
  </div>
  <h2 class="css-irv07">Contents</h2>
  <div class="section-header_mb-section-header__Wk_hk">
    <h2 class="title_mb-section-header__title__73sdX">Leaders</h2>
  </div>
  <div class="teaser_mb-teaser__k_8Tk">
    <img src="https://www.economist.com/content-assets/images/20261121_LDD001.jpg">
    <h3 class="headline_mb-teaser__headline__HY3DI">
      <a href="/leaders/2026/11/19/can-britannia-rule-the-waves-again">Can Britannia rule the waves again?</a>
    </h3>
  </div>
  <div class="section-header_mb-section-header__Wk_hk">
    <h2 class="title_mb-section-header__title__73sdX">Empty section</h2>
  </div>
  <div class="section-header_mb-section-header__Wk_hk">
    <h2 class="title_mb-section-header__title__73sdX">United States</h2>
  </div>
  <div class="teaser_mb-teaser__k_8Tk">
    <h3 class="headline_mb-teaser__headline__HY3DI">
      <a href="https://www.economist.com/united-states/2026/11/19/measles">The return of measles &amp; more</a>
    </h3>
  </div>
</main></body></html>
"""


def test_is_active():
    assert PROVIDER.is_active(SOURCE)
    assert PROVIDER.is_active(SOURCE + "/")
    assert not PROVIDER.is_active("https://www.economist.com/weeklyedition/2026-11-14")
    assert not PROVIDER.is_active("https://example.com/weeklyedition")


def test_process_single_edition_item():
    [item] = PROVIDER.process(SAMPLE_HTML, SOURCE)
    assert item.title == "Weekly edition, November 21, 2026: Axis of malice"
    assert item.url == "https://www.economist.com/weeklyedition/2026-11-21"
    assert item.published_at == datetime(2026, 11, 21)
    assert item.image_url == COVER


def test_process_description_lists_articles_by_section():
    [item] = PROVIDER.process(SAMPLE_HTML, SOURCE)
    desc = item.description
    assert desc.startswith(f'<p><img src="{COVER}"')
    assert "<h3>Leaders</h3>" in desc
    assert (
        '<a href="https://www.economist.com/leaders/2026/11/19/can-britannia-rule-the-waves-again">'
        "Can Britannia rule the waves again?</a>"
    ) in desc
    assert "The return of measles &amp; more" in desc
    assert desc.index("Leaders") < desc.index("United States")
    assert "Empty section" not in desc
    assert "Contents" not in desc


def test_process_without_date_falls_back_to_source_url():
    [item] = PROVIDER.process(SAMPLE_HTML.replace("November 21st 2026", ""), SOURCE)
    assert item.url == SOURCE
    assert item.published_at is None
    assert item.title == "Weekly edition: Axis of malice"


def test_process_empty():
    assert PROVIDER.process("<html></html>", SOURCE) == []
