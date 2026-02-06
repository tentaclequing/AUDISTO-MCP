import json
import pytest
from audisto_client import AudistoClient
from models import CrawlSummary, CrawlStatusResponse

import requests
import responses


def test_get_crawl_summary_v2_success():
    """Test successful crawl summary retrieval."""
    client = AudistoClient(api_key="k", password="p")
    crawl_id = 123
    url = f"https://api.audisto.com/2.0/crawls/{crawl_id}"
    payload = {"domain": "example.com", "crawled_pages": 42, "max_depth": 5, "start_time": "2024-01-01"}

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=payload, status=200)
        data = client.get_crawl_summary_v2(crawl_id)
        assert isinstance(data, CrawlSummary)
        assert data.domain == "example.com"
        assert data.crawled_pages == 42


def test_get_crawl_summary_v2_not_found():
    """Test 404 error handling for non-existent crawl."""
    client = AudistoClient(api_key="k", password="p")
    crawl_id = 999
    url = f"https://api.audisto.com/2.0/crawls/{crawl_id}"

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, status=404)
        with pytest.raises(requests.exceptions.HTTPError):
            client.get_crawl_summary_v2(crawl_id)


def test_get_crawl_summary_v2_invalid_id_negative():
    """Test validation error for negative crawl ID."""
    client = AudistoClient(api_key="k", password="p")
    with pytest.raises(ValueError, match="crawl_id must be a positive integer"):
        client.get_crawl_summary_v2(-1)


def test_get_crawl_summary_v2_invalid_id_non_integer():
    """Test validation error for non-integer crawl ID."""
    client = AudistoClient(api_key="k", password="p")
    with pytest.raises(ValueError, match="crawl_id must be a positive integer"):
        client.get_crawl_summary_v2("not_an_int")  # type: ignore


def test_get_crawl_status_v2_success_with_items():
    """Test successful crawl status retrieval with items format."""
    client = AudistoClient(api_key="k", password="p")
    url = "https://api.audisto.com/2.0/status/crawls"
    payload = {
        "items": [
            {"id": 1, "domain": "example.com", "status": "finished"},
            {"id": 2, "domain": "test.com", "status": "in_progress"}
        ]
    }

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=payload, status=200)
        data = client.get_crawl_status_v2()
        assert isinstance(data, CrawlStatusResponse)
        assert len(data.items) == 2
        assert data.items[0].domain == "example.com"


def test_get_crawl_status_v2_success_with_list():
    """Test successful crawl status retrieval with direct list format."""
    client = AudistoClient(api_key="k", password="p")
    url = "https://api.audisto.com/2.0/status/crawls"
    payload = [
        {"id": 1, "domain": "example.com", "status": "finished"},
        {"id": 2, "domain": "test.com", "status": "in_progress"}
    ]

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=payload, status=200)
        data = client.get_crawl_status_v2()
        # Should wrap list in CrawlStatusResponse
        assert isinstance(data, CrawlStatusResponse)
        assert len(data.items) == 2


def test_get_crawl_status_v2_rate_limit():
    """Test 429 rate limit error handling with retry exhaustion."""
    client = AudistoClient(api_key="k", password="p")
    url = "https://api.audisto.com/2.0/status/crawls"

    with responses.RequestsMock() as rsps:
        # Note: The retry adapter will retry 429s, so we need to add multiple responses
        rsps.add(rsps.GET, url, status=429)
        rsps.add(rsps.GET, url, status=429)
        rsps.add(rsps.GET, url, status=429)
        rsps.add(rsps.GET, url, status=429)  # Final retry

        # When retries are exhausted, RetryError is raised instead of HTTPError
        with pytest.raises(requests.exceptions.RetryError):
            client.get_crawl_status_v2()


def test_iter_chunked_stops():
    """Test chunked iteration stops at correct boundary."""
    client = AudistoClient(api_key="k", password="p")
    path = "/crawls/1/pages/"
    url = "https://api.audisto.com/2.0" + path

    # first chunk
    first = {"chunk": {"total": 3, "page": 0, "size": 2}, "items": [{"id": 1}, {"id": 2}]}
    second = {"chunk": {"total": 3, "page": 1, "size": 2}, "items": [{"id": 3}]}

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=first, status=200)
        rsps.add(rsps.GET, url, json=second, status=200)

        items = list(client.iter_chunked(path, chunksize=2))
        assert len(items) == 3


def test_iter_chunked_invalid_chunksize_too_large():
    """Test validation error for chunk size exceeding API limit."""
    client = AudistoClient(api_key="k", password="p")
    with pytest.raises(ValueError, match="chunksize must be between 1 and 10,000"):
        list(client.iter_chunked("/crawls/1/pages", chunksize=20000))


def test_iter_chunked_invalid_chunksize_zero():
    """Test validation error for zero chunk size."""
    client = AudistoClient(api_key="k", password="p")
    with pytest.raises(ValueError, match="chunksize must be between 1 and 10,000"):
        list(client.iter_chunked("/crawls/1/pages", chunksize=0))


def test_iter_chunked_unexpected_response_format():
    """Test error handling for unexpected response format."""
    client = AudistoClient(api_key="k", password="p")
    path = "/crawls/1/pages/"
    url = "https://api.audisto.com/2.0" + path

    with responses.RequestsMock() as rsps:
        # Return a list instead of dict
        rsps.add(rsps.GET, url, json=[{"id": 1}], status=200)

        with pytest.raises(RuntimeError, match="Unexpected chunked response format"):
            list(client.iter_chunked(path, chunksize=100))
