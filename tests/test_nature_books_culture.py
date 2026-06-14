import textwrap
from datetime import datetime

from feedminer.providers.nature_books_culture import NatureBooksCultureProvider

PROVIDER = NatureBooksCultureProvider()

SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <div class="c-article-item__wrapper">
      <div class="c-article-item__container">
        <div class="c-article-item__content c-article-item--with-image">
          <a data-track="click" href="/articles/d41586-026-01911-z">
            <div class="c-article-item__image-container mb10">
              <div class="u-responsive-ratio">
                <img alt="" class="c-article-item__image figure__image" loading="lazy"
                  src="//media.nature.com/w580h326/magazine-assets/d41586-026-01911-z/d41586-026-01911-z_52538522.jpg"/>
              </div>
            </div>
            <div class="c-article-item__copy">
              <h3 class="c-article-item__title mb10">Why we seek to fly: Books in brief</h3>
              <div class="c-article-item__standfirst">
                <p>Andrew Robinson reviews five of the best science picks.</p>
              </div>
              <div class="c-article-item__footer">
                <span class="c-article-item__article-type sans-serif strong">Book Review</span>
                <span class="pl6 pr6 c-article-item__spacer">|</span>
                <span class="c-article-item__date">12 JUN 2026</span>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
    <div class="c-article-item__wrapper">
      <div class="c-article-item__container">
        <div class="c-article-item__content c-article-item--with-image">
          <a data-track="click" href="/articles/d41586-026-01718-y">
            <div class="c-article-item__image-container mb10">
              <div class="u-responsive-ratio">
                <img alt="" class="c-article-item__image figure__image" loading="lazy"
                  src="//media.nature.com/w580h326/magazine-assets/d41586-026-01718-y/d41586-026-01718-y_52500226.jpg"/>
              </div>
            </div>
            <div class="c-article-item__copy">
              <h3 class="c-article-item__title mb10">Doubting Thomas</h3>
              <div class="c-article-item__footer">
                <span class="c-article-item__article-type sans-serif strong">Futures</span>
                <span class="pl6 pr6 c-article-item__spacer">|</span>
                <span class="c-article-item__date">10 JUN 2026</span>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
    </body></html>
""")


def test_is_active_matches_books_culture():
    assert PROVIDER.is_active("https://www.nature.com/books-culture")
    assert PROVIDER.is_active("https://www.nature.com/books-culture/")


def test_is_active_rejects_other_nature_paths():
    assert not PROVIDER.is_active("https://www.nature.com/news")
    assert not PROVIDER.is_active("https://www.nature.com/articles/d41586-026-01911-z")


def test_is_active_rejects_other_domains():
    assert not PROVIDER.is_active("https://example.com/books-culture")


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert len(items) == 2


def test_process_title():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert items[0].title == "Why we seek to fly: Books in brief"


def test_process_url_resolves_relative():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert items[0].url == "https://www.nature.com/articles/d41586-026-01911-z"


def test_process_description():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert items[0].description == "Andrew Robinson reviews five of the best science picks."
    assert items[1].description is None


def test_process_date():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert items[0].published_at == datetime(2026, 6, 12)


def test_process_image_adds_https_scheme():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.nature.com/books-culture")
    assert items[0].image_url == "https://media.nature.com/w580h326/magazine-assets/d41586-026-01911-z/d41586-026-01911-z_52538522.jpg"


def test_process_no_cards_returns_empty():
    items = PROVIDER.process("<html><body></body></html>", "https://www.nature.com/books-culture")
    assert items == []
