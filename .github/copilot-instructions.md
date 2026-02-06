# AUDISTO-MCP: Codebase Guide

## Project Overview
AUDISTO-MCP is an MCP server that connects AI agents to Audisto's technical SEO API (v2.0). It provides three tools: `get_help()`, `get_crawl_status()`, and `get_crawl_summary()`.

Note: This project is a read-only adapter. Tools only fetch and summarize Audisto data — there are no functions to start, stop, or modify crawls.

## Key Files
- **`server.py`** - MCP server entry point; defines the three tools and credential validation
- **`audisto_client.py`** - Centralized HTTP client with retry logic, session pooling, and threading lock
- **`models.py`** - Pydantic models for response validation
- **`requirements.txt`** - Pinned dependencies (requests, fastmcp, pydantic)
- **`docs/audisto_endpoints.json`** - Canonical API v2.0 endpoint reference

## How It Works
1. Tools call `get_client()` which returns an `AudistoClient` instance
2. Client uses a threading lock to enforce Audisto's "1 request per API key at a time" limit
3. Retries (3x) with exponential backoff on 429, 5xx errors
4. All responses are logged; errors return user-friendly messages

## Development
- Run tests: `pip install -r requirements-dev.txt && pytest`
- Run server: `python server.py` (requires `AUDISTO_API_KEY` and `AUDISTO_PASSWORD` env vars)
- CI: `.github/workflows/ci.yml` runs pip-audit and pytest on push/PR

## When Audisto API Changes
1. Update the base URL or endpoints in `audisto_client.py` (lines 20-21)
2. Update `docs/audisto_endpoints.json` with new endpoints
3. Add/update tests in `tests/test_audisto_client.py`
4. CI will catch breaking changes via pip-audit and test failures

