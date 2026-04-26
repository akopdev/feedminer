import textwrap

from feedminer.providers.mit_press import MITProvider

PROVIDER = MITProvider()

SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <div class="isbn-grid per-row-5" id="isbn-grid-11044">
      <div class="book-wrapper">
        <div class="image-wrapper">
          <a href="/9780262553858/the-tales-teeth-tell" target="_blank" title="The Tales Teeth Tell">
            <picture class="sp__the-cover">
              <img alt="The Tales Teeth Tell" class="lazyload"
                data-src="https://mit-press-us.imgix.net/covers/9780262553858.jpg?auto=format&w=145"
                src="lazy-placeholder.jpg"/>
            </picture>
          </a>
        </div>
        <div class="info-wrapper">
          <p class="sp__the-title"><a href="/9780262553858/the-tales-teeth-tell">The Tales Teeth Tell</a></p>
          <p class="sp__the-author">Tanya M. Smith</p>
          <p class="sp__the-publication-date">January 21, 2025</p>
        </div>
      </div>
      <div class="book-wrapper">
        <div class="image-wrapper">
          <a href="/9780262549844/macroeconomic-modeling" target="_blank" title="Macroeconomic Modeling">
            <picture class="sp__the-cover">
              <img alt="Macroeconomic Modeling" class="lazyload"
                data-src="https://mit-press-us.imgix.net/covers/9780262549844.jpg?auto=format&w=145"
                src="lazy-placeholder.jpg"/>
            </picture>
          </a>
        </div>
        <div class="info-wrapper">
          <p class="sp__the-title"><a href="/9780262549844/macroeconomic-modeling">Macroeconomic Modeling</a></p>
          <p class="sp__the-author">Ray C. Fair</p>
          <p class="sp__the-publication-date">January 21, 2025</p>
        </div>
      </div>
    </div>
    </body></html>
""")

ACCESS_DENIED_HTML = (
    "<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY><H1>Access Denied</H1></BODY></HTML>"
)


def test_is_active_matches_mit():
    assert PROVIDER.is_active("https://mitpress.mit.edu/new-releases/")
    assert PROVIDER.is_active("https://mitpress.mit.edu/books/some-book")


def test_is_active_rejects_others():
    assert not PROVIDER.is_active("https://mit.edu")
    assert not PROVIDER.is_active("https://example.com")


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_HTML, "https://mitpress.mit.edu/new-releases/")
    assert len(items) == 2


def test_process_correct_fields():
    items = PROVIDER.process(SAMPLE_HTML, "https://mitpress.mit.edu/new-releases/")
    first = items[0]
    assert first.title == "The Tales Teeth Tell"
    assert first.url == "https://mitpress.mit.edu/9780262553858/the-tales-teeth-tell"
    assert first.author == "Tanya M. Smith"
    assert first.published_at.year == 2025
    assert first.published_at.month == 1
    assert first.published_at.day == 21
    assert first.image_url == "https://mit-press-us.imgix.net/covers/9780262553858.jpg"


def test_process_image_strips_query_params():
    items = PROVIDER.process(SAMPLE_HTML, "https://mitpress.mit.edu/new-releases/")
    assert "?" not in items[0].image_url


def test_process_access_denied_returns_empty():
    items = PROVIDER.process(ACCESS_DENIED_HTML, "https://mitpress.mit.edu/new-releases/")
    assert items == []


def test_process_no_grid_returns_empty():
    items = PROVIDER.process(
        "<html><body><p>Nothing here</p></body></html>", "https://mitpress.mit.edu/new-releases/"
    )
    assert items == []
