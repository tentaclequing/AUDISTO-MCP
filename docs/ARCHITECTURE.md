# Architecture Guide

This document explains the design, structure, and reasoning behind AUDISTO-MCP.

## Project Overview

AUDISTO-MCP is a **read-only Model Context Protocol (MCP) server** that bridges AI agents (Claude, Gemini) to Audisto's technical SEO API. It enables SEO professionals to query crawl data and results without needing to manually interact with APIs.

**Key Principle**: Safe, read-only access. Users cannot start, stop, or modify crawls—only retrieve and analyze data.

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│   AI Agents (Claude/Gemini)         │
│   (via MCP protocol)                │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   MCP Server (server.py)            │
│   - Tool definitions                │
│   - Credential validation           │
│   - Error handling & formatting     │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Audisto Client (audisto_client.py)│
│   - HTTP session + retries          │
│   - Request queueing (thread lock)  │
│   - Chunk size validation           │
│   - Response parsing                │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Audisto API v2.0                  │
│   (https://api.audisto.com/2.0)     │
└─────────────────────────────────────┘
```

---

## Core Components

### 1. **server.py** — MCP Interface Layer
**Responsibility**: Define tools, handle user-facing communication, validate credentials

**Key Functions**:
- `get_help()` → Displays available commands and usage examples
- `get_crawl_status()` → Lists 5 most recent crawls (safe default limit)
- `get_crawl_summary(crawl_id)` → Returns details for a specific crawl
- `get_auth()` → Retrieves API credentials from environment
- `get_client()` → Instantiates `AudistoClient`
- `validate_startup_credentials()` → Fails fast if credentials are missing

**Design Rationale**:
- All tools return `str` (human-readable formatted text, not raw JSON)
- Specific exception handling (not bare `except Exception`)
- Structured logging at appropriate levels (info, warning, error, critical)
- Startup validation prevents runtime surprises

### 2. **audisto_client.py** — HTTP Client Layer
**Responsibility**: Safe, reliable communication with Audisto API

**Key Features**:
- **Session Pooling**: Reuses `requests.Session` to reduce overhead
- **Retry Logic**: Exponential backoff on 429 (Too Many Requests) and 5xx errors (up to 3 retries)
- **Thread-Safe Request Queueing**: Threading lock enforces "1 request per API key at a time" (Audisto's requirement)
- **Chunk Size Validation**: Rejects requests with chunksize > 10,000 (API limit)
- **Timeout**: 120-second timeout per request (respects Audisto's 2-minute API timeout)

**Key Methods**:
- `get_crawl_status_v2()` → Fetch crawl list
- `get_crawl_summary_v2(crawl_id)` → Fetch crawl details
- `iter_chunked(path, chunksize)` → Safely iterate over paginated results

**Design Rationale**:
- Centralized client allows easy updates if Audisto API changes
- Retries + backoff handle transient failures gracefully
- Threading lock prevents concurrent requests (Audisto enforces 1 per key)
- Explicit chunksize validation prevents silent API rejections

### 3. **models.py** — Data Validation
**Responsibility**: Define expected response shapes using Pydantic

**Models**:
- `CrawlSummary`: Fields for crawl metadata (id, domain, pages, depth, start_time)
- `ChunkMeta`: Fields for pagination metadata (total, page, size)

**Design Rationale**:
- Catches malformed responses early
- Type safety for IDE autocompletion
- Easy to extend when Audisto adds new fields

### 4. **tests/test_audisto_client.py** — Unit Tests
**Responsibility**: Verify client behavior in isolation

**Tests**:
- `test_get_crawl_summary_v2_success()` — Mocked successful response
- `test_iter_chunked_stops()` — Pagination stops at correct boundary

**Design Rationale**:
- Uses `responses` library to mock HTTP calls (no live API dependency)
- CI runs tests automatically on every push/PR
- Prevents regressions when updating client code

---

## Data Flow Example

### Scenario: User asks Claude, "Show me my recent crawls"

1. **Claude Desktop / Gemini CLI** → Discovers available MCP tools
2. **Agent** → Calls `get_crawl_status()` tool
3. **server.py** `get_crawl_status()`:
   - Calls `get_client()`
   - Client calls `get_auth()` → Retrieves env vars
   - Acquires thread lock (wait if another request is running)
4. **audisto_client.py** `get_crawl_status_v2()`:
   - Constructs URL: `https://api.audisto.com/2.0/status/crawls`
   - Sends GET request with Basic Auth
   - Releases lock when done
5. **Audisto API** → Returns JSON list of crawls
6. **audisto_client.py** → Parses JSON, returns dict
7. **server.py** `get_crawl_status()`:
   - Formats response for AI readability (status icons, labels)
   - Returns human-friendly string
8. **Claude/Gemini** → Displays results to user

---

## API Limits & Safety

### Audisto API Constraints (from API docs)
- **1 request per key at a time**: If you send a second request before the first finishes, you get a 429 error
- **Max chunk size: 10,000** items per request
- **Timeout: 2 minutes** per request

### How We Enforce Them

| Constraint | Implementation | Where |
|-----------|-----------------|-------|
| 1 request/key | Threading lock | `audisto_client.py` line 42 |
| Max 10K chunks | Validation in `iter_chunked()` | `audisto_client.py` line 105-107 |
| 2-min timeout | `timeout=120` in session | `audisto_client.py` line 54 |
| Single instance | Warning in README + docstring | README.md, audisto_client.py module doc |

### User Responsibility
- **Only run one MCP instance per API key** at a time
- If you use Claude Desktop AND Gemini CLI with the same credentials, they may conflict
- Client includes retries to handle transient 429 errors automatically

---

## Security Considerations

### Credentials
- ✅ Never logged or exposed in error messages
- ✅ Validated at startup (fails fast if missing)
- ✅ Retrieved from environment variables only (not hardcoded)
- ✅ `.env` files added to `.gitignore`

### Error Handling
- ✅ Specific exception types caught (not bare `except Exception`)
- ✅ User-friendly error messages (no technical details leaked)
- ✅ Structured logging for diagnostics (server operators only)

### Dependency Scanning
- ✅ CI runs `pip-audit` on every push (detects vulnerable packages)
- ✅ Dependencies pinned to specific versions (reproducible installs)
- ✅ No external services called (Audisto API only)

### API Safety
- ✅ Read-only operations (no mutation endpoints)
- ✅ Thread-safe request queueing
- ✅ Chunk size validation before sending

---

## Future Roadmap

### v1.2 (Potential)
- [ ] Add `get_pages(crawl_id)` to retrieve paginated page data
- [ ] Add `get_links(crawl_id)` for link graph analysis
- [ ] Cache recent crawl lists (reduce API calls)
- [ ] Support for additional Audisto endpoints (hints, checks, requirements)

### v2.0 (Long-term)
- [ ] Cached page content retrieval (`/cached/rendering/html/parsed`)
- [ ] History/trend analysis (`/2.0/histories`)
- [ ] Monitoring checks and alerts (`/2.0/crawls/{id}/checks`)

### Not Planned (By Design)
- [ ] Start/stop crawl endpoints (read-only philosophy)
- [ ] Configuration modification (read-only philosophy)
- [ ] Web UI (MCP is the interface)

---

## Contributing & Maintenance

### Adding a New Tool

1. Implement client method in `audisto_client.py`:
   ```python
   def get_my_data(self, param: int) -> Dict[str, Any]:
       """Docstring with API behavior."""
       url = self._url("/my/endpoint")
       with self._lock:
           resp = self.session.get(url, auth=self.auth, timeout=self.timeout)
       resp.raise_for_status()
       return resp.json()
   ```

2. Wrap in `server.py` MCP tool:
   ```python
   @mcp.tool()
   def my_tool(param: int) -> str:
       """User-facing description."""
       try:
           client = get_client()
           data = client.get_my_data(param)
           # Format and return
           return formatted_response
       except [specific exceptions]:
           # Handle errors
   ```

3. Add tests in `tests/test_audisto_client.py`
4. Update `docs/audisto_endpoints.json`
5. Update `README.md` and `CHANGELOG.md`

### When Audisto API Changes

1. Update endpoint URLs in `audisto_client.py` (lines 20-21: `DEFAULT_BASE`, `DEFAULT_VERSION`)
2. Update `docs/audisto_endpoints.json` with new endpoints
3. Add/update tests
4. CI will catch breaking changes via test failures
5. Update `CHANGELOG.md` with breaking changes

---

## Testing Strategy

- **Unit Tests**: Mocked responses, no API dependency (fast, reliable)
- **CI Tests**: Run on every push/PR (pip-audit + pytest)
- **Manual Smoke Test** (future): Real API calls with read-only operations, scheduled nightly
- **No E2E Tests**: Too risky with live Audisto accounts; mocking is sufficient

---

## Deployment Notes

### Local Development
```bash
pip install -r requirements.txt
python server.py  # Requires AUDISTO_API_KEY + AUDISTO_PASSWORD
```

### Claude Desktop
Add to `claude_desktop_config.json`

### Gemini CLI
```bash
gemini mcp add audisto "python /path/to/server.py"
gemini mcp enable audisto
```

### Docker (Future)
Could containerize for easier distribution, but not planned for v1.1

---

## References

- [Audisto API v2.0 Docs](https://api.audisto.com)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlopp/fastmcp)
- [Pydantic Docs](https://docs.pydantic.dev/)
