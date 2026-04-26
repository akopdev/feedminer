from feedminer.models import Feed, FeedItem


def test_feed_to_rss_valid_structure():
    feed = Feed(
        title="Test Feed",
        url="https://example.com",
        description="A test feed",
        items=[
            FeedItem(title="Item 1", url="https://example.com/1", author="Alice"),
            FeedItem(title="Item 2", url="https://example.com/2"),
        ],
    )
    xml = feed.to_rss()
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<rss " in xml and 'version="2.0"' in xml
    assert "<channel>" in xml
    assert "<title>Test Feed</title>" in xml
    assert "<link>https://example.com</link>" in xml
    assert "Item 1" in xml
    assert "Item 2" in xml
    assert "<author>Alice</author>" in xml


def test_feed_to_rss_empty_items():
    feed = Feed(title="Empty Feed", url="https://example.com")
    xml = feed.to_rss()
    assert "<item>" not in xml


def test_feed_to_rss_image():
    feed = Feed(
        title="Feed",
        url="https://example.com",
        items=[
            FeedItem(
                title="X", url="https://example.com/x", image_url="https://example.com/img.jpg"
            )
        ],
    )
    xml = feed.to_rss()
    assert "media:content" in xml
    assert "https://example.com/img.jpg" in xml
