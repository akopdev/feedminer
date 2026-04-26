import textwrap

from feedminer.providers.yale import YaleProvider

PROVIDER = YaleProvider()

SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <div class="isbn-grid per-row-5" id="isbn-grid-199">
      <div class="book-wrapper left">
        <div class="image-wrapper">
          <a href="/book/9781588398116/raphael" tabindex="0" title="Cover of Raphael">
            <picture class="sp__the-cover">
              <img alt="Cover of Raphael" class="lazyload" data-baseline-images="image"
                data-src="https://yale-press-us.imgix.net/covers/9781588398116.jpg?auto=format&w=145"
                src="lazy-placeholder.jpg"/>
            </picture>
          </a>
        </div>
        <div class="info-wrapper">
          <div class="book-info">
            <p class="sp__the-title">Raphael</p>
            <p class="sp__the-subtitle">Sublime Poetry</p>
            Carmen C. Bambach
          </div>
        </div>
      </div>
      <div class="book-wrapper left">
        <div class="image-wrapper">
          <a href="/book/9780300278552/atlas-of-the-transatlantic-slave-trade" tabindex="0">
            <picture class="sp__the-cover">
              <img alt="Cover" class="lazyload" data-baseline-images="image"
                data-src="https://yale-press-us.imgix.net/covers/9780300278552.jpg?auto=format&w=145"
                src="lazy-placeholder.jpg"/>
            </picture>
          </a>
        </div>
        <div class="info-wrapper">
          <div class="book-info">
            <p class="sp__the-title">Atlas of the Transatlantic Slave Trade</p>
            David Eltis, David Richardson, Philip Misevich
          </div>
        </div>
      </div>
    </div>
    </body></html>
""")


def test_is_active_matches_yale():
    assert PROVIDER.is_active("https://yalebooks.yale.edu/books/new-releases/")
    assert PROVIDER.is_active("https://yalebooks.yale.edu/book/9781588398116/raphael")


def test_is_active_rejects_others():
    assert not PROVIDER.is_active("https://yale.edu")
    assert not PROVIDER.is_active("https://example.com")


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_HTML, "https://yalebooks.yale.edu/books/new-releases/")
    assert len(items) == 2


def test_process_correct_fields():
    items = PROVIDER.process(SAMPLE_HTML, "https://yalebooks.yale.edu/books/new-releases/")
    first = items[0]
    assert first.title == "Raphael"
    assert first.url == "https://yalebooks.yale.edu/book/9781588398116/raphael"
    assert first.author == "Carmen C. Bambach"
    assert first.image_url == "https://yale-press-us.imgix.net/covers/9781588398116.jpg"


def test_process_image_strips_query_params():
    items = PROVIDER.process(SAMPLE_HTML, "https://yalebooks.yale.edu/books/new-releases/")
    assert "?" not in items[0].image_url


def test_process_multiple_authors():
    items = PROVIDER.process(SAMPLE_HTML, "https://yalebooks.yale.edu/books/new-releases/")
    assert items[1].author == "David Eltis, David Richardson, Philip Misevich"


def test_process_no_grid_returns_empty():
    items = PROVIDER.process("<html><body></body></html>", "https://yalebooks.yale.edu/books/new-releases/")
    assert items == []
