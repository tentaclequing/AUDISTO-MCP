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

import logging
import os
import threading
from typing import Any, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models import CrawlStatusResponse, CrawlSummary

# Configure logging
logger = logging.getLogger(__name__)

# Suppress urllib3 debug logging to prevent auth header leakage
logging.getLogger("urllib3").setLevel(logging.WARNING)

DEFAULT_BASE = "https://api.audisto.com"
DEFAULT_VERSION = os.getenv("AUDISTO_API_VERSION", "2.0")


class AudistoClient:
    def __init__(
        self,
        api_key: str | None = None,
        password: str | None = None,
        base_url: str = DEFAULT_BASE,
        api_version: str = DEFAULT_VERSION,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout

        # Get credentials from parameters or environment
        final_api_key = api_key or os.getenv("AUDISTO_API_KEY")
        final_password = password or os.getenv("AUDISTO_PASSWORD")

        # Store as tuple for requests auth (None if missing)
        self.auth: tuple[str, str] | None = (
            (final_api_key, final_password)
            if final_api_key and final_password
            else None
        )
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

    def get_crawl_status_v2(self) -> CrawlStatusResponse | dict[str, Any]:
        """Retrieve list of recent crawls (v2).

        Returns a validated CrawlStatusResponse model or raw dict if validation fails.
        """
        url = self._url("/status/crawls")
        logger.debug(f"Fetching crawl status from {url}")

        with self._lock:
            resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
        resp.raise_for_status()

        data: Any = resp.json()
        logger.info("Successfully fetched crawl status")

        # Try to validate with Pydantic, fall back to raw dict if format differs
        try:
            if isinstance(data, dict) and "items" in data:
                return CrawlStatusResponse(**data)
            elif isinstance(data, list):
                # If API returns a list directly, wrap it
                return CrawlStatusResponse(items=data)
            # Return as dict if not handled above
            return dict(data) if not isinstance(data, dict) else data
        except Exception as e:
            logger.warning(f"Failed to validate crawl status response: {e}. Returning raw data.")
            # Ensure we return a dict type
            return dict(data) if not isinstance(data, dict) else data

    def get_crawl_summary_v2(self, crawl_id: int) -> CrawlSummary:
        """Retrieve crawl details for a given crawl id (v2).

        Returns a validated CrawlSummary model.

        Raises:
            ValueError: If crawl_id is invalid
            requests.exceptions.HTTPError: If API request fails
        """
        if not isinstance(crawl_id, int) or crawl_id < 0:
            raise ValueError("crawl_id must be a positive integer")

        url = self._url(f"/crawls/{crawl_id}")
        logger.debug(f"Fetching crawl summary for ID {crawl_id} from {url}")

        with self._lock:
            resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
        resp.raise_for_status()

        data = resp.json()
        logger.info(f"Successfully fetched crawl summary for ID {crawl_id}")

        return CrawlSummary(**data)

    def iter_chunked(self, path: str, chunksize: int = 100, **params: Any) -> Iterator[dict[str, Any]]:
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

        logger.debug(f"Starting chunked iteration on {path} with chunksize={chunksize}")
        page = 0
        total_items = 0

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
            total_items += len(items)
            logger.debug(f"Fetched page {page}: {len(items)} items (total so far: {total_items})")

            yield from items

            chunk_meta = data.get("chunk", {})
            total = chunk_meta.get("total")
            size = chunk_meta.get("size")
            page = chunk_meta.get("page", page)

            # Stop if we have no items or we've reached the last page
            if not items or total is None or (size is not None and (page + 1) * size >= total):
                logger.info(f"Completed chunked iteration: {total_items} total items")
                break
            page += 1


__all__ = ["AudistoClient"]
