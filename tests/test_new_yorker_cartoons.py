from datetime import datetime

from feedminer.providers.new_yorker_cartoons import NewYorkerDailyCartoonProvider

PROVIDER = NewYorkerDailyCartoonProvider()
SOURCE = "https://www.newyorker.com/cartoons/daily-cartoon"

SAMPLE_HTML = """
<html><body>
<div class="summary-item summary-list__item">
  <div class="summary-item__content">
    <a class="summary-item__hed-link" href="/cartoons/daily-cartoon/friday-october-2nd-stand-it">
      <h3 class="summary-item__hed">Daily Cartoon: Friday, October 2nd</h3>
    </a>
    <time>October 2, 2026</time>
  </div>
  <picture><img alt="x" src="https://media.newyorker.com/cartoons/abc/4:3/w_1600%2Ch_1200%2Cc_limit/undefined"/></picture>
</div>
<div class="summary-item summary-list__item"><div class="ad">no headline</div></div>
<div class="summary-item summary-list__item">
  <div class="summary-item__content">
    <a class="summary-item__hed-link" href="https://www.newyorker.com/cartoons/daily-cartoon/thursday-october-1st-only-poll">
      <h3 class="summary-item__hed">Daily Cartoon: Thursday, October 1st</h3>
    </a>
  </div>
</div>
</body></html>
"""


def test_is_active():
    assert PROVIDER.is_active(SOURCE)
    assert PROVIDER.is_active(SOURCE + "/")
    assert not PROVIDER.is_active("https://www.newyorker.com/cartoons")
    assert not PROVIDER.is_active("https://example.com/cartoons/daily-cartoon")


def test_process_skips_cards_without_headline():
    assert len(PROVIDER.process(SAMPLE_HTML, SOURCE)) == 2


def test_process_fields():
    first, second = PROVIDER.process(SAMPLE_HTML, SOURCE)
    assert first.title == "Daily Cartoon: Friday, October 2nd"
    assert first.url == "https://www.newyorker.com/cartoons/daily-cartoon/friday-october-2nd-stand-it"
    assert first.published_at == datetime(2026, 10, 2)
    assert first.image_url.startswith("https://media.newyorker.com/cartoons/abc")
    assert second.url.endswith("thursday-october-1st-only-poll")
    assert second.published_at is None and second.image_url is None


def test_process_empty():
    assert PROVIDER.process("<html></html>", SOURCE) == []


DETAIL_HTML = """
<html><head><meta name="description" content="Enrico Pinto’s Daily Cartoon riffs on caterpillars."/></head><body>
<div class="responsive-cartoon">
  <img alt="From within a cocoon a frightened caterpillar stares out." src="https://media.newyorker.com/cartoons/abc/master/w_1600%2Cc_limit/A62289.jpg"/>
  <div class="responsive-cartoon__caption"><span class="caption__text"> “How can you stand it out there?”</span></div>
  <div class="responsive-cartoon__credit"><span class="caption__credit">Cartoon by Enrico Pinto</span></div>
</div></body></html>
"""


class FakeScraper:
    async def fetch(self, url):
        if url.endswith("thursday-october-1st-only-poll"):
            raise RuntimeError("boom")
        return DETAIL_HTML


def test_enrich_adds_caption_credit_and_description():
    import asyncio

    items = PROVIDER.process(SAMPLE_HTML, SOURCE)
    first, second = asyncio.run(PROVIDER.enrich(items, FakeScraper()))
    assert "<b>“How can you stand it out there?”</b>" in first.description
    assert "frightened caterpillar" in first.description
    assert "Cartoon by Enrico Pinto" in first.description
    assert first.author == "Enrico Pinto"
    assert "/master/" in first.image_url
    # a failed page fetch leaves the listing data intact
    assert second.description is None and second.url.endswith("only-poll")
