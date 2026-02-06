import json
from audisto_client import AudistoClient

import responses


def test_get_crawl_summary_v2_success():
    client = AudistoClient(api_key="k", password="p")
    crawl_id = 123
    url = f"https://api.audisto.com/2.0/crawls/{crawl_id}"
    payload = {"domain": "example.com", "crawled_pages": 42}

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=payload, status=200)
        data = client.get_crawl_summary_v2(crawl_id)
        assert data["domain"] == "example.com"
        assert data["crawled_pages"] == 42


def test_iter_chunked_stops():
    client = AudistoClient(api_key="k", password="p")
    path = "/crawls/1/pages/"
    url = "https://api.audisto.com/2.0" + path

    # first chunk
    first = {"chunk": {"total": 3, "page": 0, "size": 2}, "items": [{"id":1}, {"id":2}]}
    second = {"chunk": {"total": 3, "page": 1, "size": 2}, "items": [{"id":3}]}

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, url, json=first, status=200)
        rsps.add(rsps.GET, url, json=second, status=200)

        items = list(client.iter_chunked(path, chunksize=2))
        assert len(items) == 3
