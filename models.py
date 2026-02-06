from pydantic import BaseModel
from typing import Optional


class CrawlSummary(BaseModel):
    id: Optional[int]
    domain: Optional[str]
    crawled_pages: Optional[int]
    max_depth: Optional[int]
    start_time: Optional[str]


class ChunkMeta(BaseModel):
    total: Optional[int]
    page: Optional[int]
    size: Optional[int]
