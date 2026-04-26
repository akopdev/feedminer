import textwrap

from feedminer.providers.hup_harvard import HUPHarvardProvider

# Minimal HTML mirroring the real page structure
SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <article data-component="cards:book-card" itemscope itemtype="https://schema.org/Book">
      <img class="cover-img" data-src="https://www.hup.harvard.edu/img/feeds/jackets/123.png">
      <a href="https://www.hup.harvard.edu/books/9780674046238" itemtype="url">
        <h2 itemprop="name">The First Social Democracy</h2>
      </a>
      <span itemprop="author">Stephen F. Jones</span>
    </article>
    <article data-component="cards:book-card" itemscope itemtype="https://schema.org/Book">
      <img class="cover-img" data-src="https://www.hup.harvard.edu/img/feeds/jackets/456.png">
      <a href="/books/9780674999999" itemtype="url">
        <h2 itemprop="name">Another Great Book</h2>
      </a>
      <span itemprop="author">Jane Smith</span>
    </article>
    </body></html>
""")

PROVIDER = HUPHarvardProvider()


def test_is_active_matches_hup():
    assert PROVIDER.is_active("https://www.hup.harvard.edu/new-releases?sort=date")
    assert PROVIDER.is_active("https://hup.harvard.edu/books/123")


def test_is_active_rejects_others():
    assert not PROVIDER.is_active("https://example.com")
    assert not PROVIDER.is_active("https://harvard.edu")


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.hup.harvard.edu/new-releases")
    assert len(items) == 2


def test_process_correct_fields():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.hup.harvard.edu/new-releases")
    first = items[0]
    assert first.title == "The First Social Democracy"
    assert first.url == "https://www.hup.harvard.edu/books/9780674046238"
    assert first.author == "Stephen F. Jones"
    assert first.image_url == "https://www.hup.harvard.edu/img/feeds/jackets/123.png"


def test_process_relative_url_is_resolved():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.hup.harvard.edu/new-releases")
    second = items[1]
    assert second.url.startswith("https://www.hup.harvard.edu")


def test_process_empty_html_returns_empty():
    items = PROVIDER.process("<html><body></body></html>", "https://www.hup.harvard.edu")
    assert items == []
