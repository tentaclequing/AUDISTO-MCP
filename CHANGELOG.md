# Changelog

All notable changes to AUDISTO-MCP are documented in this file.

## [1.1.0] - 2026-02-06

### Added
- **Centralized API Client** (`audisto_client.py`): Replaces direct HTTP calls with a robust, reusable client that handles authentication, retries, and session pooling
- **Request Queueing**: Threading lock ensures Audisto's "1 request per API key at a time" limit is respected within a single MCP instance
- **Automatic Retries**: Exponential backoff (3 retries) on timeout and server errors (429, 5xx)
- **Chunk Size Validation**: Validates chunk sizes (max 10,000 items) before sending requests to prevent API errors
- **Pydantic Models** (`models.py`): Response validation and structured data handling
- **Unit Tests** (`tests/test_audisto_client.py`): Mocked tests for the client with pytest
- **CI/CD Pipeline** (`.github/workflows/ci.yml`): Automated testing and security scanning (pip-audit) on every push/PR
- **Help Tool** (`get_help()`): Displays available commands and usage examples for users
- **Development Dependencies** (`requirements-dev.txt`): pytest, responses, pip-audit for local testing
- **API Documentation** (`docs/audisto_endpoints.json`): Canonical reference of Audisto API v2.0 endpoints
- **Gemini CLI Support**: Full integration instructions for Gemini CLI (in addition to Claude Desktop)
- **Security Hardening**:
  - Startup credential validation (fails fast if credentials missing)
  - `.gitignore` entries for `.env`, virtual environments, and build artifacts
  - Credential validation via threading lock (prevents accidental logging)
  - Security checklist in README for users publishing this tool

### Changed
- **Server refactoring**: `server.py` now uses `AudistoClient` instead of direct `requests` calls
- **Error handling**: Specific exception types (Timeout, HTTPError, RequestException, ValueError) instead of bare `Exception`
- **Logging**: Structured logging with appropriate levels (info, warning, error, critical)
- **API version**: Explicitly set to v2.0 (previously v1.0)

### Fixed
- **Consistent status code handling**: Standardized `getattr(e.response, 'status_code', None)` across error handlers
- **Removed redundant logging**: Consolidated startup messages
- **Proper exit code**: Changed `exit(1)` to `sys.exit(1)` for production standards

### Documentation
- **README.md**: Added usage limits, security checklist, Gemini CLI setup, and help tool docs
- **Copilot Instructions**: Simplified for local AI agent development
- **Module docstrings**: Clear explanations of purpose, features, and constraints

## [1.0.0] - 2026-02-05

### Added
- **Initial Release**: Basic MCP server for Audisto integration
- **Three MCP Tools**:
  - `get_crawl_status()`: Lists recent crawls
  - `get_crawl_summary(crawl_id)`: Retrieves crawl details
  - `get_help()`: Displays help text
- **Basic Error Handling**: Try-catch blocks for API calls
- **CLI Integration**: Claude Desktop configuration support
- **MIT License**: Open-source, permissive licensing
