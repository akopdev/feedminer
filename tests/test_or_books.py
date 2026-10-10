from feedminer.providers.or_books import ORBooksProvider

PROVIDER = ORBooksProvider()
SOURCE_URL = "https://orbooks.com/catalog/?sort=newest"

SAMPLE_HTML = """
<ul class="productGrid">
<li class="product"><article class="card" data-entity-id="2086"><div class="sub-card">
<figure class="card-figure"><a href="https://orbooks.com/catalog/their-blood-our-bullets/" class="card-figure__link">
<img src="https://cdn.example/80w/a.jpg" class="lazyload card-image"
 data-srcset="https://cdn.example/80w/a.jpg 80w, https://cdn.example/640w/a.jpg 640w, https://cdn.example/960w/a.jpg 960w"></a></figure>
<div class="card-body"><h3 class="card-title">
<a class="card-title-name" href="https://orbooks.com/catalog/their-blood-our-bullets/">
  Their Blood, Our Bullets
</a></h3>
<div class="card-category custom-author-field">
<div class="card-category-name">The Hidden Story of the US–Russia War for Ukraine</div>
<div class="card-text"><a href="/authors/m/aaron-mate/">Aaron Maté</a></div>
</div></div></div></article></li>
<li class="product"><article class="card"><div class="sub-card">
<div class="card-body"><h3 class="card-title">
<a class="card-title-name" href="https://orbooks.com/catalog/bare/">Bare</a></h3></div>
</div></article></li>
</ul>
"""


def test_is_active():
    assert PROVIDER.is_active("https://orbooks.com/catalog/")
    assert PROVIDER.is_active(SOURCE_URL)
    assert not PROVIDER.is_active("https://orbooks.com/about/")
    assert not PROVIDER.is_active("https://example.com/catalog/")


def test_feed_filename():
    assert PROVIDER.feed_filename == "or-books-catalog"


def test_process_extracts_fields():
    items = PROVIDER.process(SAMPLE_HTML, SOURCE_URL)
    assert len(items) == 2
    first = items[0]
    assert first.title == "Their Blood, Our Bullets"
    assert first.url == "https://orbooks.com/catalog/their-blood-our-bullets/"
    assert first.author == "Aaron Maté"
    assert first.description == "The Hidden Story of the US–Russia War for Ukraine"
    assert first.image_url == "https://cdn.example/640w/a.jpg"


def test_process_minimal_card():
    bare = PROVIDER.process(SAMPLE_HTML, SOURCE_URL)[1]
    assert bare.title == "Bare"
    assert bare.author is None
    assert bare.description is None
    assert bare.image_url is None


def test_process_no_grid():
    assert PROVIDER.process("<html></html>", SOURCE_URL) == []
