from typing import List, Optional

from pydantic import BaseModel, Field


class CrawlStatus(BaseModel):
    """Individual crawl status item from the crawl list endpoint."""
    id: Optional[int] = None
    domain: Optional[str] = None
    status: Optional[str] = None


class CrawlStatusResponse(BaseModel):
    """Response from the crawl status endpoint."""
    items: List[CrawlStatus] = Field(default_factory=list)


class CrawlSummary(BaseModel):
    """Detailed summary of a specific crawl."""
    id: Optional[int] = None
    domain: Optional[str] = None
    crawled_pages: Optional[int] = None
    max_depth: Optional[int] = None
    start_time: Optional[str] = None


class ChunkMeta(BaseModel):
    """Pagination metadata for chunked responses."""
    total: Optional[int] = None
    page: Optional[int] = None
    size: Optional[int] = None
