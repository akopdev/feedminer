import textwrap

from feedminer.providers.stanford import StanfordProvider

PROVIDER = StanfordProvider()

SAMPLE_HTML = textwrap.dedent("""\
    <html><body>
    <ul>
      <li>
        <div class="mx-auto max-w-3xl">
          <div class="relative">
            <div class="rs-mb-1 relative aspect-[2/3] w-full">
              <img alt="" class="ed11y-ignore object-cover"
                src="/_next/image?url=https%3A%2F%2Fsupress.sites-pro.stanford.edu%2Ffiles%2Fmedia%2Fcovers%2F36755.jpg&amp;w=3840&amp;q=75"
                style="position:absolute;height:100%;width:100%;"/>
            </div>
            <h2><a href="/books/middle-east-studies/colonial-constructs">Colonial Constructs</a></h2>
          </div>
          <div class="rs-mb-0 text-[0.8em] text-press-sand-dark">Stone, Cement, Labor, and Race in Modern Palestine/Israel</div>
          <div class="mb-0 text-[0.8em] text-press-sand-dark">Nimrod Ben Zeev</div>
        </div>
      </li>
      <li>
        <div class="mx-auto max-w-3xl">
          <div class="relative">
            <div class="rs-mb-1 relative aspect-[2/3] w-full">
              <img alt="" class="ed11y-ignore object-cover"
                src="/_next/image?url=https%3A%2F%2Fsupress.sites-pro.stanford.edu%2Ffiles%2Fmedia%2Fcovers%2F30730.jpg&amp;w=3840&amp;q=75"/>
            </div>
            <h2><a href="/books/middle-east-studies/anatomy-empire">Anatomy of Empire</a></h2>
          </div>
          <div class="rs-mb-0 text-[0.8em] text-press-sand-dark">Sex and Medicine in the Late Ottoman World</div>
          <div class="mb-0 text-[0.8em] text-press-sand-dark">Seçil Yılmaz</div>
        </div>
      </li>
    </ul>
    </body></html>
""")


def test_is_active_matches_stanford():
    assert PROVIDER.is_active("https://www.sup.org/books/subjects/middle-east-studies")
    assert PROVIDER.is_active("https://sup.org/books/history/some-book")


def test_is_active_rejects_others():
    assert not PROVIDER.is_active("https://stanford.edu")
    assert not PROVIDER.is_active("https://example.com")


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.sup.org/books/subjects/middle-east-studies")
    assert len(items) == 2


def test_process_correct_fields():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.sup.org/books/subjects/middle-east-studies")
    first = items[0]
    assert first.title == "Colonial Constructs"
    assert first.url == "https://www.sup.org/books/middle-east-studies/colonial-constructs"
    assert first.author == "Nimrod Ben Zeev"
    assert first.description == "Stone, Cement, Labor, and Race in Modern Palestine/Israel"
    assert first.image_url == "https://supress.sites-pro.stanford.edu/files/media/covers/36755.jpg"


def test_process_image_decoded_from_nextjs_proxy():
    items = PROVIDER.process(SAMPLE_HTML, "https://www.sup.org/books/subjects/middle-east-studies")
    assert "/_next/image" not in items[0].image_url
    assert items[0].image_url.startswith("https://supress")


def test_process_no_cards_returns_empty():
    items = PROVIDER.process("<html><body><ul></ul></body></html>", "https://www.sup.org/books/subjects/middle-east-studies")
    assert items == []
