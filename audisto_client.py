"""Small Audisto API v2 client used by the MCP server.

Features:
- Centralized base URL + API version constants
- `requests.Session` with retry/backoff
- In-process single-request lock (Audisto allows 1 request per key at a time)
- Chunk validation (max 10,000 items per request)
- Helpers: `get_crawl_status_v2`, `get_crawl_summary_v2`, and a `iter_chunked` helper

IMPORTANT: The threading lock only enforces single-request ordering within ONE MCP instance.
If you run multiple MCP servers with the same API key, you must ensure they do not send
requests simultaneously, or Audisto will return 429 (Too Many Requests) errors.
"""
from __future__ import annotations

import os
import threading
from typing import Any, Dict, Iterator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_BASE = "https://api.audisto.com"
DEFAULT_VERSION = "2.0"


class AudistoClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        base_url: str = DEFAULT_BASE,
        api_version: str = DEFAULT_VERSION,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout
        self.auth = (api_key or os.getenv("AUDISTO_API_KEY"), password or os.getenv("AUDISTO_PASSWORD"))
        self._lock = threading.Lock()

        # Session with retries/backoff
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{self.api_version}{path}"

    def get_crawl_status_v2(self) -> Dict[str, Any]:
        """Retrieve list of recent crawls (v2).

        Returns the parsed JSON response as a dict/list. Does not format for UI.
        """
        url = self._url("/status/crawls")
        with self._lock:
            resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_crawl_summary_v2(self, crawl_id: int) -> Dict[str, Any]:
        """Retrieve crawl details for a given crawl id (v2).

        Returns parsed JSON dict.
        """
        if not isinstance(crawl_id, int) or crawl_id < 0:
            raise ValueError("crawl_id must be a positive integer")
        url = self._url(f"/crawls/{crawl_id}")
        with self._lock:
            resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def iter_chunked(self, path: str, chunksize: int = 100, **params) -> Iterator[Dict[str, Any]]:
        """Iterate over chunked endpoints.

        Args:
            path: API endpoint path, e.g., "/crawls/{id}/pages/"
            chunksize: Number of items per chunk (default 100, max 10,000 per Audisto API limits)
            **params: Additional query parameters

        Yields:
            Dict items from the 'items' array in each chunk response.

        Raises:
            ValueError: If chunksize > 10,000 (Audisto API maximum)
            RuntimeError: On unexpected response format
        """
        # Validate chunksize against Audisto API limit
        if chunksize < 1 or chunksize > 10000:
            raise ValueError(f"chunksize must be between 1 and 10,000 (got {chunksize})")
        
        page = 0
        while True:
            p = dict(params)
            p.update({"chunk": page, "chunksize": chunksize})
            url = self._url(path)
            with self._lock:
                resp = self.session.get(url, auth=self.auth, timeout=self.timeout, params=p)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError("Unexpected chunked response format")
            items = data.get("items", [])
            yield from items
            chunk_meta = data.get("chunk", {})
            total = chunk_meta.get("total")
            size = chunk_meta.get("size")
            page = chunk_meta.get("page", page)
            # Stop if we have no items or we've reached the last page
            if not items or total is None or (size is not None and (page + 1) * size >= total):
                break
            page += 1


__all__ = ["AudistoClient"]
