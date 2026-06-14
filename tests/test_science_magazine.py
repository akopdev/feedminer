import json
from datetime import datetime

from feedminer.providers.science_magazine import ScienceMagazineProvider

PROVIDER = ScienceMagazineProvider()

SAMPLE_ISSUE = {
    "groupId": 77723,
    "issueName": "June 11, 2026",
    "description": None,
    "url": "/sciencemagazine/11_june_2026",
    "issueUrl": "11_june_2026",
    "publishDate": 1780963200000,
    "publication": "sciencemagazine",
    "publicationDisplayName": "Science Magazine",
    "publicationId": 26268,
    "ticketId": "158806",
    "userHasAccess": False,
    "accessLevel": "restricted",
    "replicaOnly": False,
    "documentLink": "https://www.sciencemagazinedigital.org/sciencemagazine/11_june_2026",
    "coverImage": "https://images-cdn.dashdigital.com/sciencemagazine/11_june_2026/cover468w.gif",
    "pdfDownloadUrl": "",
    "docType": "Default",
}

SAMPLE_ISSUE_WITH_DESC = {
    **SAMPLE_ISSUE,
    "groupId": 77684,
    "issueName": "June 4, 2026",
    "description": "Special issue on climate.",
    "publishDate": 1780358400000,
    "documentLink": "https://www.sciencemagazinedigital.org/sciencemagazine/04_june_2026",
    "coverImage": "https://images-cdn.dashdigital.com/sciencemagazine/04_june_2026/cover468w.gif",
}

SOURCE_URL = "https://www.sciencemagazinedigital.org/sciencemagazine/gtxapi/issuelist"

SAMPLE_JSON = json.dumps({"groupDetails": [SAMPLE_ISSUE, SAMPLE_ISSUE_WITH_DESC]})


def test_is_active_matches_issuelist():
    assert PROVIDER.is_active(SOURCE_URL)


def test_is_active_rejects_other_paths():
    assert not PROVIDER.is_active("https://www.sciencemagazinedigital.org/sciencemagazine/library/")
    assert not PROVIDER.is_active("https://www.sciencemagazinedigital.org/")


def test_is_active_rejects_other_domains():
    assert not PROVIDER.is_active("https://example.com/sciencemagazine/gtxapi/issuelist")


def test_feed_filename():
    assert PROVIDER.feed_filename == "science-magazine-issues"


def test_process_extracts_items():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert len(items) == 2


def test_process_title():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[0].title == "June 11, 2026"


def test_process_url():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[0].url == "https://www.sciencemagazinedigital.org/sciencemagazine/11_june_2026"


def test_process_image():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[0].image_url == "https://images-cdn.dashdigital.com/sciencemagazine/11_june_2026/cover468w.gif"


def test_process_date():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[0].published_at == datetime(2026, 6, 9, 0, 0)


def test_process_description_none():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[0].description is None


def test_process_description_present():
    items = PROVIDER.process(SAMPLE_JSON, SOURCE_URL)
    assert items[1].description == "Special issue on climate."


def test_process_invalid_json_returns_empty():
    items = PROVIDER.process("not json", SOURCE_URL)
    assert items == []


def test_process_empty_groupdetails_returns_empty():
    items = PROVIDER.process(json.dumps({"groupDetails": []}), SOURCE_URL)
    assert items == []
